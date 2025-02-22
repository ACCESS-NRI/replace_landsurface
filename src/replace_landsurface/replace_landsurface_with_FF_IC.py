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
        return sources[0]
    def transform(self, sources, result):
        return sources[1]

def replace_in_ff_from_ff(f, sf, mf_out, replace):
    replacement_data = sf.get_data()
    mf_out.fields.append(replace([f, replacement_data]))

def swap_land_ff(ic_file_fullpath, source_fullpath):
    """
    Function to get the land/surface data from another fields file into the start dump.

    Parameters
    ----------
    ic_file_fullpath : Path
        Path to file with the coarser resolution data to be replaced with ".tmp" appended at end
    source_fullpath : Path
        Path to source fields file to take the land/surface data from

    Returns
    -------
    None.
        The file is replaced with a version of itself holding the higher-resolution data.
    """
   
    # Path to input file 
    ff_in = ic_file_fullpath.as_posix().replace('.tmp', '')

    # Path to output file 
    ff_out = ic_file_fullpath.as_posix()

    # Path to source input file 
    sf_in = source_fullpath.as_posix()

    # Read input file
    mf_in = mule.load_umfile(ff_in)
    # Read source file
    msf_in = mule.load_umfile(sf_in)
   
    # Set up the output file
    mf_out = mf_in.copy()
    
    # Create Mule Replacement Operator
    replace = ReplaceOperator() 

    # For each field in the input write to the output file (but modify as required)
    for f,sf in zip(mf_in.fields,msf_in.fields):
        if f.lbuser4 in [9, 20, 24]:
            replace_in_ff_from_ff(f, sf, mf_out, replace)
        else:
            mf_out.fields.append(f)
   
    # Write output file
    mf_out.validate = lambda *args, **kwargs: True
    mf_out.to_file(ff_out)
