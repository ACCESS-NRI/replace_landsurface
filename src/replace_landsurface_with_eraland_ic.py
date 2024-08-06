"""Module for replacing land/surface fields with data from the era5-land netcdf archive. """
# pylint: disable=trailing-whitespace
# pylint: disable=too-many-locals
# pylint: disable=too-many-statements
import os
import sys
from glob import glob
from pathlib import Path
import iris # pylint: disable=import-error
import mule # pylint: disable=import-error
import numpy as np # pylint: disable=import-error
import xarray as xr # pylint: disable=import-error
import common_mule_operator # pylint: disable=import-error

ROSE_DATA = os.environ.get('ROSE_DATA')
# Base directory of the ERA5-land archive on NCI
ERA_DIR = os.path.join(ROSE_DATA, 'etc', 'era5_land')

# The depths of soil for the conversion
##########multipliers=[7.*10., 21.*10., 72.*10., 189.*10.]
multipliers = [10.*10., 25.*10., 65.*10., 200.*10.]

class BoundingBoxEra5land():
    """ Container class to hold spatial extent information."""
    def __init__(self):
        """ Initialize BoundingBoxEra5land object"""
        # Set the boundaries
        self.lonmin=np.nan
        self.lonmax=np.nan
        self.latmin=np.nan
        self.latmax=np.nan
    def set_bounds(self, ncfname, maskfname, var):
        """
        Set bounds for bounding_box class
        
        Parameters
        ----------
        ncfname : POSIX string
            POSIX path to input data (from the NetCDF archive)
        maskfname : POSIX string
            POSIX path to mask information to define the data to be cut out
        var : string
            The name of the mask variable that defines the spatial extent
        
        Returns
        -------
        None.  
            The variables describing the spatial extent are definied within bounding box object.
        """
        
        # Read in the mask and get the minimum/maximum latitude and longitude information
        if Path(maskfname).exists():
            d = iris.load(maskfname, var)
            d = d[0]
            d = xr.DataArray.from_iris(d)
            
            lons = d['longitude'].data
            lonmin = np.min(lons)
            lonmax = np.max(lons)
            
            if lonmax > 180.:
                lonmax = lonmax-360.
                
            lats = d['latitude'].data
            latmin = np.min(lats)
            latmax = np.max(lats)
            d.close()
        else:
            print(f'ERROR: File {maskfname} not found', file=sys.stderr)
            sys.exit(1)
        
        # Read in the file from the high-res netcdf archive
        if Path(ncfname).exists():
            d = xr.open_dataset(ncfname)
        else:
            print(f'ERROR: File {ncfname} not found', file=sys.stderr)
            sys.exit(1)
            
        # Get the longitude information
        lons = d['longitude'].data
        
        # Coping with numerical inaccuracy
        adj = (lons[1] - lons[0])/2.
        
        # Work out which longitudes define the minimum/maximum extents of the grid of interest
        lonmin_index = np.argwhere((lons > lonmin - adj) & (lons < lonmin + adj))[0][0]
        lonmax_index = np.argwhere((lons > lonmax - adj) & (lons < lonmax + adj))[0][0]
        
        # Get the latitude information
        lats = d['latitude'].data
        
        # Work out which longitudes define the minimum/maximum extents of the grid of interest
        # use the same adjustment as for longitude
        latmin_index = np.argwhere((lats > latmin - adj) & (lats < latmin + adj))[0][0]
        latmax_index = np.argwhere((lats > latmax - adj) & (lats < latmax + adj))[0][0]

        # Swap the latitude min/max if upside down (is upside down for era5-land)
        if latmax_index < latmin_index:
            tmp_index=latmin_index
            latmin_index=latmax_index
            latmax_index=tmp_index
        
        # Set the boundaries
        self.lonmin=lonmin_index
        self.lonmax=lonmax_index
        self.latmin=latmin_index
        self.latmax=latmax_index
    def get_lons(self):
        return(self.lonmin,self.lonmax)
    def get_lats(self):
        return(self.latmin,self.latmax)


def get_era_nc_data(ncfname, fieldn, wanted_dt, bounds): 
    """
    Function to get the ERA5-land data for a single land/surface variable.
    
    Parameters
    ----------
    ncfname : string
        The name of the file to read
    FIELDN : string
        The name of the variable in the file to read
    wanted_dt : string
        The date-time required in "%Y%m%d%H%M" format
    bounds : bounding_box object
        A bounding box object defining the spatial extent to keep
        
    Returns
    -------
    2d numpy array
        A 2-D numpy array containg the field data for the date/time and spatial extent
    """
    
    # retrieve the spatial extends of interest
    lonmin_index, lonmax_index = bounds.get_lons()
    latmin_index, latmax_index = bounds.get_lats()
    
    # Open the file containing the data
    print(ncfname, fieldn)
    if Path(ncfname).exists():
        d = xr.open_dataset(ncfname)
    else:
        print(f'ERROR: File {ncfname} not found', file=sys.stderr)
        sys.exit(1)
        
    # Find the array index for the date/time of interest
    times=d['time'].dt.strftime("%Y%m%d%H%M").data
    tm=times.tolist().index(wanted_dt)
    print(tm)
    
    # Read the data
    if lonmin_index < lonmax_index:
        # Grid does not wrap around.  Simple read.
        try:
            data=d[fieldn][tm, latmin_index:latmax_index+1, lonmin_index:lonmax_index+1]
            data=data.data
        except KeyError:
            print(ncfname)
            print('ERROR: Variable temp not found in file', file=sys.stderr)
            sys.exit(1)
    else:
        # Data required wraps around the input grid.  Read in sections and patch together.
        try:
            data_left=d[fieldn][tm, latmin_index:latmax_index+1, lonmin_index:].data
            data_right=d[fieldn][tm, latmin_index:latmax_index+1, 0:lonmax_index+1].data
            data=np.concatenate((data_left, data_right), axis=1)
        except KeyError:
            print(ncfname)
            print('ERROR: Variable temp not found in file', file=sys.stderr)
            sys.exit(1)
            
    d.close()
    
    # Flip the data vertically because the era5-land 
    # latitudes are reversed in direction to the UM FF
    return data[::-1, :]

def replace_in_ff_from_era5land(f, generic_era5_fname, era_fieldn, \
                                multiplier, ic_z_date, mf_out, replace, bounds):
    current_data = f.get_data()
    era5_fname = generic_era5_fname.replace('FIELDN', era_fieldn)
    data = get_era_nc_data(era5_fname, era_fieldn, ic_z_date, bounds)
    if multiplier < 0:
        pass
    else:
        data = data * multiplier
        
    data = np.where(np.isnan(data), current_data, data)
    mf_out.fields.append(replace([f, data]))
    
def swap_land_era5land(mask_fullpath, ic_file_fullpath, ic_date):
    """
    Function to get the ERA5-land data for all land/surface variables.
    
    Parameters
    ----------
    mask_fullpath : Path
        Path to the mask defining the spatial extent
    ic_file_fullpath : string
        Path to file with the coarser resolution data to be replaced with ".tmp" appended at end
    ic_date : string
        The date-time required in "%Y%m%d%H%M" format
        
    Returns
    -------
    None.
        The file is replaced with a version of itself holding the higher-resolution data.
    """
    
    # create date/time useful information
    print(ic_date)
    yyyy = ic_date[0:4]
    mm = ic_date[4:6]
    ic_z_date = ic_date.replace('T', '').replace('Z', '')
    
    # Find one "swvl1" file in the archive and create a generic filename
    era_fieldn = 'swvl1'
    land_yes = os.path.join(ERA_DIR, era_fieldn, yyyy)
    era_files = glob(os.path.join(land_yes, era_fieldn + '*' + yyyy + mm + '*nc'))
    era5_fname = os.path.join(land_yes, os.path.basename(era_files[0]))
    generic_era5_fname = era5_fname.replace('swvl1', 'FIELDN')
    
    # Path to input file
    ff_in = ic_file_fullpath.as_posix().replace('.tmp', '')
    
    # Path to output file
    ff_out = ic_file_fullpath.as_posix()
    print(ff_in, ff_out)
    
    # Read input file
    mf_in = mule.load_umfile(ff_in)
    
    # Create Mule Replacement Operator
    replace = common_mule_operator.ReplaceOperator()
    
    # Define spatial extent of grid required
    bounds = BoundingBoxEra5land()
    bounds.set_bounds(era5_fname, mask_fullpath.as_posix(), "land_binary_mask")
    
    # Set up the output file
    mf_out = mf_in.copy()
    
    # For each field in the input write to the output file (but modify as required)
    for f in mf_in.fields:
        if f.lbuser4 == 9:
            # replace coarse soil moisture with high-res information
            soil_level=f.lblev
            replace_in_ff_from_era5land(f, generic_era5_fname, 'swvl%d'%soil_level, \
                                        multipliers[soil_level-1], ic_z_date, mf_out, replace, bounds)
        elif f.lbuser4 == 20:
            # soil temperature
            soil_level=f.lblev
            replace_in_ff_from_era5land(f, generic_era5_fname, 'stl%d'%soil_level, \
                                        -1, ic_z_date, mf_out, replace, bounds)
        elif f.lbuser4 == 24:
            # surface temperature
            replace_in_ff_from_era5land(f, generic_era5_fname, 'skt', \
                                        -1, ic_z_date, mf_out, replace, bounds)
        else:
            mf_out.fields.append(f)
    # Write output file
    mf_out.validate = lambda *args, **kwargs: True
    mf_out.to_file(ff_out)
