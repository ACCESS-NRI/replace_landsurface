# Copyright 2024 ACCESS-NRI (https://www.access-nri.org.au/)
# See the top-level COPYRIGHT.txt file for details.
#
# SPDX-License-Identifier: Apache-2.0
#
# Created by: Chermelle Engel <Chermelle.Engel@anu.edu.au>

import mule

class ReplaceOperator(mule.DataOperator):
    """ Mule operator for replacing the data"""
    def __init__(self):
        pass
    def new_field(self, sources):
        print('new_field')
        return sources[0]
    def transform(self, sources, result):
        print('transform')
        return sources[1]

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
    replace = ReplaceOperator() 

    # Set up the output file
    mf_out = mf_in.copy()

    # For each field in the input write to the output file (but modify as required)
    for f,sf in zip(mf_in.fields,msf_in.fields):
    
        if f.lbuser4 in [9, 20, 24]:
            replace_in_ff_from_ff(f, sf, mf_out, replace)
        else:
            mf_out.fields.append(f)
   
    # Write output file
    mf_out.validate = lambda *args, **kwargs: True
    mf_out.to_file(ff_out)
