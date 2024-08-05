import iris
import mule
import os
import sys
import numpy as np
from pathlib import Path
import xarray as xr, sys, argparse
from datetime import datetime,timedelta
import common_mule_operator

def replace_in_ff_from_ff(f, sf, mf_out, replace):
#def replace_in_ff(f, generic_era5_fname, ERA_FIELDN, multiplier, ic_z_date, mf_out, replace, bounds):

    replacement_data = sf.get_data()
    mf_out.fields.append(replace([f, replacement_data]))

def swap_land_ff(mask_fullpath, ic_file_fullpath, source_fullpath,ic_date):
    """
    Function to get the land/surface data from another fields file into the start dump.

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

    print(mask_fullpath, ic_file_fullpath, source_fullpath,ic_date)

    # create name of file to be replaced
    ic_file = ic_file_fullpath.parts[-1].replace('.tmp', '')
   
    # create date/time useful information
    print(ic_date)
    yyyy = ic_date[0:4]
    mm = ic_date[4:6]
    ic_z_date = ic_date.replace('T', '').replace('Z', '')
   
    # Path to input file 
    ff_in = ic_file_fullpath.as_posix().replace('.tmp', '')

    # Path to input file 
    sf_in = source_fullpath.as_posix()

    # Path to output file 
    ff_out = ic_file_fullpath.as_posix()
    print(ff_in, ff_out)
   
    # Read input file
    mf_in = mule.load_umfile(ff_in)
    msf_in = mule.load_umfile(sf_in)
   
    # Create Mule Replacement Operator
    replace = common_mule_operator.ReplaceOperator() 

    # Define spatial extent of grid required
    #bounds = bounding_box(era5_fname, mask_fullpath.as_posix(), "land_binary_mask")

    # Set up the output file
    mf_out = mf_in.copy()

    # For each field in the input write to the output file (but modify as required)
    for f,sf in zip(mf_in.fields,msf_in.fields):
    
      print(f.lbuser4, f.lblev, f.lblrec, f.lbhr, f.lbcode)

      if f.lbuser4 == 9:
        # replace coarse soil moisture with high-res information
        if f.lblev == 4:
          replace_in_ff_from_ff(f, sf, mf_out, replace)
        elif f.lblev == 3:
          replace_in_ff_from_ff(f, sf, mf_out, replace)
        elif f.lblev == 2:
          replace_in_ff_from_ff(f, sf, mf_out, replace)
        elif f.lblev == 1:
          replace_in_ff_from_ff(f, sf, mf_out, replace)

      elif f.lbuser4 == 20:
        # soil temperature
        if f.lblev == 4:
          replace_in_ff_from_ff(f, sf, mf_out, replace)
        elif f.lblev == 3:
          replace_in_ff_from_ff(f, sf, mf_out, replace)
        elif f.lblev == 2:
          replace_in_ff_from_ff(f, sf, mf_out, replace)
        elif f.lblev == 1:
          replace_in_ff_from_ff(f, sf, mf_out, replace)

      elif f.lbuser4 == 24:
        replace_in_ff_from_ff(f, sf, mf_out, replace)
      else:
        mf_out.fields.append(f)
   
    # Write output file
    mf_out.validate = lambda *args, **kwargs: True
    mf_out.to_file(ff_out)
