# Copyright 2024 ACCESS-NRI (https://www.access-nri.org.au/)
# See the top-level COPYRIGHT.txt file for details.
#
# SPDX-License-Identifier: Apache-2.0
#
# Created by: Chermelle Engel <Chermelle.Engel@anu.edu.au>

#!/usr/bin/env python3

"""
Replace the land/surface fields in the astart file with higher-resolution
era5-land or BARRA2-R data (if requested).
"""

from pathlib import Path
import argparse
from datetime import datetime
import shutil
import replace_landsurface_with_ERA5land_IC 
import replace_landsurface_with_BARRA2R_IC

INPUT_TIME_FORMAT = "%Y%m%d%H%M"
OUTPUT_TIME_FORMAT = "%Y%m%dT%H%MZ"

def get_start_time(time):
    """
    Convert the time from the input string format to the desired string format

    Parameters
    ----------
    time: str
        The time in the input string format

    Returns
    -------
    str
        The time in the desired string format
    """
    return datetime.strptime(time,INPUT_TIME_FORMAT).strftime(OUTPUT_TIME_FORMAT)

def replace_input_file_with_tmp_input_file(tmp_path):
    """
    Swaps the newly-created temporary input file with the original input file, by
    removing the '.tmp' extension from the temporary file path.

    Parameters
    ----------
    tmp_path: PosixPath
        The temporary path with the '.tmp' extension.

    Returns
    -------
    None
    """
    if tmp_path.suffix == '.tmp':
        shutil.move(tmp_path, tmp_path.with_suffix(''))
    else:
        raise ValueError(f"Expected a path ending in '.tmp', got '{tmp_path}'.")

def parse_arguments():
    """
    Parses the command line arguments.

    Parameters
    ----------
    None

    Returns
    -------
    argparse.Namespace
        The parsed command line arguments
    """
    # Parse the command-line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--mask', required=True, type=Path)
    parser.add_argument('--file', required=True, type=Path)
    parser.add_argument('--start', required=True, type=str)
    parser.add_argument('--type', default="era5land")
    return parser.parse_args()

def set_replace_function(data_type):
    """
    Set what replace function to use, based on the command line argument '--type'.

    Parameters
    ----------
    data_type: str
        Type of data source for the replacement. The value of the command line argument '--type'.

    Returns
    -------
    callable or None
        The function to be called for the replacement, or None if no replacement needs to take place.
    """ 
    if data_type == "era5land":
        replace_function = replace_landsurface_with_ERA5land_IC.swap_land_era5land
    elif data_type == "barra":
        replace_function = replace_landsurface_with_BARRA2R_IC.swap_land_barra
    else:
        replace_function = None
    return replace_function

    
def main():
    """
    The main function that creates a worker pool and generates single GRIB files 
    for requested date/times in parallel.

    Parameters
    ----------
    None.  The arguments are given via the command-line

    Returns
    -------
    None.  The astart file is updated and overwritten
    """ 

    args = parse_arguments()
    print(f"{args=}")

    # Convert the date/time to a formatted string
    t = get_start_time(args.start)
    print(f"mask = {args.mask}")
    print(f"replacement_file = {args.file}")
    print(f"start_time = {t}")
    
    # If necessary replace land/surface fields with higher-resolution options
    replace_function = set_replace_function(args.type)
    if replace_function is not None:
        replace_function(args.mask, args.file, t)
        replace_input_file_with_tmp_input_file(args.file)
    else:
        print("No need to swap out IC")

if __name__ == '__main__':
    main()

