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
    
    # Set up the output file
    mf_out = mf_in.copy()
    
    # For each field in the input write to the output file (but modify as required)
    for f,sf in zip(mf_in.fields,msf_in.fields):
        
        # If the field is soil moisture, soil temperature or surface temperature, then replace.
        if f.lbuser4 in [9, 20, 24]:
            replace_in_ff_from_ff(f, sf, mf_out, replace)
        else:
            mf_out.fields.append(f)
    
    # Write output file
    mf_out.validate = lambda *args, **kwargs: True
    mf_out.to_file(ff_out)
