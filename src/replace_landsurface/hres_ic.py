# Copyright 2024 ACCESS-NRI (https://www.access-nri.org.au/)
# See the top-level COPYRIGHT.txt file for details.
#
# SPDX-License-Identifier: Apache-2.0
#
# Created by: Chermelle Engel <Chermelle.Engel@anu.edu.au>

"""
Replace the land/surface fields in the astart file with higher-resolution
era5-land or BARRA2-R data (if requested).
"""

import argparse
from pathlib import Path
from replace_landsurface import replace_landsurface, replace_landsurface_with_FF_IC

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

    # Parse the command-line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', required=True, type=Path)
    parser.add_argument('--start', required=True, type=str, help="A date in the format 'YYYYmmddHHMM'.")
    parser.add_argument('--type', default="era5land")
    parser.add_argument('--hres_ic', type=Path)
    args = parser.parse_args()

    # If necessary replace ERA5 land/surface fields with higher-resolution options
    if args.type in ("era5land", "barra"):
        replace_landsurface.swap_land(args.file, args.start, args.type)
    elif args.type == "astart":
        replace_landsurface_with_FF_IC.swap_land_ff(args.file, args.hres_ic)
    else:
        raise ValueError(f"Unsupported '--type' argument: {args.type}")

if __name__ == '__main__':
    main()

