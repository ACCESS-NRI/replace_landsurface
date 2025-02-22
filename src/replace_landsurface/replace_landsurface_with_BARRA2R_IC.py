# Copyright 2024 ACCESS-NRI (https://www.access-nri.org.au/)
# See the top-level COPYRIGHT.txt file for details.
#
# SPDX-License-Identifier: Apache-2.0
#
# Created by: Chermelle Engel <Chermelle.Engel@anu.edu.au>

import os
import warnings
from glob import glob
from pathlib import Path
from collections import namedtuple

import mule
import numpy as np
import xarray as xr

DECIMAL_PRECISION = 4
STASH_LAND_MASK = 30
ROSE_DATA = os.environ.get('ROSE_DATA', "")
# Base directory of the ERA5-land archive on NCI
BARRA_DIR = os.path.join(ROSE_DATA, 'etc', 'barra_r2')

BoundingBox = namedtuple('BoundingBox', ('latmin', 'latmax', 'lonmin', 'lonmax'))

class ReplaceOperator(mule.DataOperator):
    """ Mule operator for replacing the data"""
    def __init__(self):
        pass
    def new_field(self, sources):
        return sources[0]
    def transform(self, sources, result):
        return sources[1]


def get_bounding_box(mule_file): 
    """ Get spatial extent information for the replacement.
    
    Parameters
    ----------
    mule_file : mule.UMFile object
        Input UM fields file

    Returns
    -------
    namedtuple
    The BoundingBox namedtuple
    """
    # Get extent from the land mask (stash 30) if present, otherwise use the first field
    # because the file extent sometimes is not correct
    try:
        field = [f for f in mule_file.fields if f.lbuser4 == STASH_LAND_MASK][0]
    except IndexError:
        field = mule_file.fields[0]
    # Get the latitude extent
    dlat = field.bdy
    nlat = mule_file.integer_constants.num_rows
    latmin = round(field.bzy + dlat, DECIMAL_PRECISION) # rounded to avoid numerical inaccuracy
    latmax = round(latmin + (nlat-1)*dlat, DECIMAL_PRECISION) # rounded to avoid numerical inaccuracy
    
    # Get the latitude extent
    dlon = field.bdx
    nlon = mule_file.integer_constants.num_cols
    lonmin = round(field.bzx + dlon, DECIMAL_PRECISION) # rounded to avoid numerical inaccuracy
    lonmax = round(lonmin + (nlon-1)*dlon, DECIMAL_PRECISION) # rounded to avoid numerical inaccuracy

    return BoundingBox(latmin, latmax, lonmin, lonmax)


def get_barra_data(fname, FIELDN, date, bounds):
    """
    Function to get the BARA2-R data for a single land/surface variable.

    Parameters
    ----------
    fname : string
        The name of the high-res file to read
    FIELDN : string
        The name of the variable in the file to read
    date : string
        The date in the format "YYYYmmddHHMM".
    bounds : tuple
        Tuple containing the spatial extent for the data in the form (latmin, latmax, lonmin, lonmax).

    Returns
    -------
    2d numpy array 
        A 2-D numpy array containg the field data for the date/time and spatial extent
    """

    # Open the file containing the data
    if Path(fname).exists():
        d = xr.open_dataset(fname)
    else:
        raise FileNotFoundError(f"File '{fname}' not found.")

    # Get the data
    # Select the variable
    try:
        data = d[FIELDN]
    except KeyError:
        raise ValueError(f"Variable '{FIELDN}' not found in high-resolution file '{fname}'.")
    # Select the date
    try:
        data = data.sel(time=date)
    except KeyError:
        # If the exact date is not found select the nearest date and send a warning message
        data = data.sel(time=date, method='nearest')
        actual_date = data.time.values.astype('datetime64[m]').tolist().strftime('%Y%m%d%H%M')
        warnings.warn(
            f"The date '{date}' was not found in the high-resolution file '{fname}'.\n"
            f"Using the nearest date '{actual_date}' instead."
        )
    # Select the spatial extent
    data = data.sel(
        lat=slice(bounds.latmin, bounds.latmax),
        lon=slice(bounds.lonmin, bounds.lonmax),
    )
    
    return data.data


def swap_land_barra(ec_cb_file_fullpath, date):
    """
    Function to get the BARRA2-R data for all land/surface variables.

    Parameters
    ----------
    ic_file_fullpath : string
        Path to file with the coarser resolution data to be replaced with ".tmp" appended at end
    date : string
        The date in the format "YYYYmmddHHMM".

    Returns
    -------
    None.
        The file is replaced with a version of itself holding the higher-resolution data.
    """
   
    # create date/time useful information
    yyyy = date[0:4]
    mm = date[4:6]
    
    # Path to input file
    ff_in = ec_cb_file_fullpath.as_posix().replace('.tmp', '')
    # Path to output file
    ff_out = ec_cb_file_fullpath.as_posix()
    
    # Read input file
    mf_in = mule.load_umfile(ff_in)
    
    # Set up the output file
    mf_out = mf_in.copy()
    
    # Get spatial extent for the replacement
    bounds = get_bounding_box(mf_in)
    
    # Create Mule Replacement Operator
    replace = ReplaceOperator() 

    # Read in the surface temperature data from the archive
    BARRA_FIELDN = 'ts'
    indir = os.path.join(BARRA_DIR, '1hr',BARRA_FIELDN, 'latest')
    barra_files = glob(os.path.join(indir, BARRA_FIELDN + '*' + yyyy + mm + '*nc'))
    barra_fname = indir + '/' + barra_files[0].split('/')[-1]


    # Read in the surface temperature data (and keep to use for replacement)
    data = get_barra_data(barra_fname, BARRA_FIELDN, date, bounds)
    surface_temp = data.copy()
    
    # Read in the soil moisture data (and keep to use for replacement)
    BARRA_FIELDN = 'mrsol'
    indir = os.path.join(BARRA_DIR, '3hr',BARRA_FIELDN, 'latest')
    barra_files = glob(os.path.join(indir, BARRA_FIELDN + '*' + yyyy + mm + '*nc'))
    barra_fname = indir + '/' + barra_files[0].split('/')[-1]
    data = get_barra_data(barra_fname, BARRA_FIELDN, date, bounds)
    mrsol = data.copy()

    # Read in the soil temperature data (and keep to use for replacement)
    BARRA_FIELDN = 'tsl'
    indir = os.path.join(BARRA_DIR, '3hr',BARRA_FIELDN, 'latest')
    barra_files = glob(os.path.join(indir, BARRA_FIELDN + '*' + yyyy + mm + '*nc'))
    barra_fname = indir + '/' + barra_files[0].split('/')[-1]
    data = get_barra_data(barra_fname, BARRA_FIELDN, date, bounds)
    tsl = data.copy()
    

    # For each field in the input write to the output file (but modify as required)
    for f in mf_in.fields:
    
      #print(f.lbuser4, f.lblev, f.lblrec, f.lbhr, f.lbcode)
      if f.lbuser4 == 9:
        # replace coarse soil moisture with high-res information
        current_data = f.get_data()
        data = mrsol[f.lblev-1, :, :]
        data = np.where(np.isnan(data), current_data, data)
        mf_out.fields.append(replace([f, data]))
      elif f.lbuser4 == 20:
        # replace coarse soil temperature with high-res information
        current_data = f.get_data()
        data = tsl[f.lblev-1, :, :]
        data = np.where(np.isnan(data), current_data, data)
        mf_out.fields.append(replace([f, data]))
      elif f.lbuser4 == 24:
        # replace surface temperature with high-res information
        current_data = f.get_data()
        data = surface_temp
        data = np.where(np.isnan(data), current_data, data)
        mf_out.fields.append(replace([f, data]))
      else:
        mf_out.fields.append(f)
    
    mf_out.validate = lambda *args, **kwargs: True
    mf_out.to_file(ff_out)
