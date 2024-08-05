#!/usr/bin/env python3

"""
Replace the land/surface fields in the ec_cb000 file with higher-resolution
era5-land or BARRA2-R data (if requested).
"""

import argparse
import pandas
import shutil
from pathlib import Path

import replace_landsurface_with_ERA5land_IC
import replace_landsurface_with_BARRA2R_IC
import replace_landsurface_with_FF_IC

boolopt = {
    "True": True,
    "False": False,
}


def main():
    """
    The main function takes a start dump and replaces the land/surface fields with those
    from either era5-land, BARRA-R2 or a fields file.

    Parameters
    ----------
    None.  The arguments are given via the command-line

    Returns
    -------
    None.  The ec_cb000 file is updated and overwritten
    """

    # Parse the command-line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--mask", required=True, type=Path)
    parser.add_argument("--file", required=True, type=Path)
    parser.add_argument("--start", required=True, type=pandas.to_datetime)
    parser.add_argument("--type", default="era5land")
    parser.add_argument("--hres_ic", type=Path)
    args = parser.parse_args()
    print(args)

    # Convert the date/time to a formatted string
    t = args.start.strftime("%Y%m%dT%H%MZ")
    print(args.mask, args.file, t)

    # If necessary replace ERA5 land/surface fields with higher-resolution options
    if "era5land" in args.type:
        replace_landsurface_with_ERA5land_IC.swap_land_era5land(args.mask, args.file, t)
        shutil.move(args.file.as_posix(), args.file.as_posix().replace(".tmp", ""))
    elif "barra" in args.type:
        replace_landsurface_with_BARRA2R_IC.swap_land_barra(args.mask, args.file, t)
        shutil.move(args.file.as_posix(), args.file.as_posix().replace(".tmp", ""))
    elif "astart" in args.type:
        print("Replacement job for FF input files is not processed for single-level suite.")
    else:
        print("No need to swap out IC")

if __name__ == "__main__":
    main()
