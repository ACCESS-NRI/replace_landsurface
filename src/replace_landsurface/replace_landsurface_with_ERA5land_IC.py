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
ERA_DIR = os.path.join(ROSE_DATA, 'etc', 'era5_land')

# The depths of soil for the conversion
SOIL_MULTIPLIERS = (100., 250., 650., 2000.)

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

def get_era_data(fname, FIELDN, date, bounds):
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
        data = xr.open_dataset(fname)
    else:
        raise FileNotFoundError(f"File '{fname}' not found.")

    # Get the data

    # Get data in the same structure as UM files: ascending latitude (-90 90) and positive longitude (0 360)
    if data.latitude[0] > data.latitude[1]: # descending latitude
        data = data.reindex(latitude=data.latitude[::-1]) # flip the latitude
    if any(data.longitude < 0): # negative longitude (-180 180)
        # longitude = np.round(data.longitude, DECIMAL_PRECISION)
        longitude = data.longitude
        new_index = [lon for lon in longitude if lon >= 0] + [lon for lon in longitude if lon < 0] # move negative longitudes to the end
        data = data.reindex(longitude=new_index)
        new_longitude = [lon if lon >= 0 else (360+lon) for lon in new_index] # convert negative longitudes to positives > 180
        data = data.assign_coords(longitude=new_longitude)
    # Select the variable
    try:
        data = data[FIELDN]
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
        latitude=slice(bounds.latmin, bounds.latmax),
        longitude=slice(bounds.lonmin, bounds.lonmax),
    )
    return data.data

def replace_in_ff(f, generic_era5_fname, ERA_FIELDN, multiplier, date, mf_out, replace, bounds):

    current_data = f.get_data()
    era5_fname = generic_era5_fname.replace('FIELDN', ERA_FIELDN)
    data = get_era_data(era5_fname, ERA_FIELDN, date, bounds)
    if multiplier < 0:
        pass
    else:
      data = data * multiplier
    data = np.where(np.isnan(data), current_data, data)
    mf_out.fields.append(replace([f, data]))

def swap_land_era5land(ic_file_fullpath, date):
    """
    Function to get the ERA5-land data for all land/surface variables.

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
    ff_in = ic_file_fullpath.as_posix().replace('.tmp', '')
    # Path to output file 
    ff_out = ic_file_fullpath.as_posix()
    
    # Read input file
    mf_in = mule.load_umfile(ff_in)

    # Set up the output file
    mf_out = mf_in.copy()
    
    # Get spatial extent for the replacement
    bounds = get_bounding_box(mf_in)

    # Create Mule Replacement Operator
    replace = ReplaceOperator()

    # Find one "swvl1" file in the archive and create a generic filename
    ERA_FIELDN = 'swvl1'
    indir = os.path.join(ERA_DIR, ERA_FIELDN, yyyy)
    era_files = glob(os.path.join(indir, ERA_FIELDN + '*' + yyyy + mm + '*nc'))
    era5_fname = os.path.join(indir, os.path.basename(era_files[0]))
    generic_era5_fname = era5_fname.replace('swvl1', 'FIELDN')
   
    # For each field in the input write to the output file (but modify as required)
    for f in mf_in.fields:

      if f.lbuser4 == 9:
        # replace coarse soil moisture with high-res information
        if f.lblev == 4:
          replace_in_ff(f, generic_era5_fname, 'swvl4', SOIL_MULTIPLIERS[3], date, mf_out, replace, bounds)
        elif f.lblev == 3:
          replace_in_ff(f, generic_era5_fname, 'swvl3', SOIL_MULTIPLIERS[2], date, mf_out, replace, bounds)
        elif f.lblev == 2:
          replace_in_ff(f, generic_era5_fname, 'swvl2', SOIL_MULTIPLIERS[1], date, mf_out, replace, bounds)
        elif f.lblev == 1:
          replace_in_ff(f, generic_era5_fname, 'swvl1', SOIL_MULTIPLIERS[0], date, mf_out, replace, bounds)

      elif f.lbuser4 == 20:
        # soil temperature
        if f.lblev == 4:
          replace_in_ff(f, generic_era5_fname, 'stl4', -1, date, mf_out, replace, bounds)
        elif f.lblev == 3:
          replace_in_ff(f, generic_era5_fname, 'stl3', -1, date, mf_out, replace, bounds)
        elif f.lblev == 2:
          replace_in_ff(f, generic_era5_fname, 'stl2', -1, date, mf_out, replace, bounds)
        elif f.lblev == 1:
          replace_in_ff(f, generic_era5_fname, 'stl1', -1, date, mf_out, replace, bounds)

      elif f.lbuser4 == 24:
        replace_in_ff(f, generic_era5_fname, 'skt', -1, date, mf_out, replace, bounds)
      else:
        mf_out.fields.append(f)
   
    # Write output file
    mf_out.validate = lambda *args, **kwargs: True
    mf_out.to_file(ff_out)
