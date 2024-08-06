#!/usr/bin/env python3

"""
Replace the land/surface fields in the astart file with higher-resolution
era5-land or BARRA2-R data (if requested).
"""

from pathlib import Path
import argparse
import shutil
import pandas # pylint: disable=import-error
import replace_landsurface_with_eraland_ic # pylint: disable=import-error
import replace_landsurface_with_barra_ic # pylint: disable=import-error
import replace_landsurface_with_ff_ic # pylint: disable=import-error

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
    None.  The astart file is updated and overwritten
    """
    # Parse the command-line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--mask", required=True, type=Path)
    parser.add_argument("--file", required=True, type=Path)
    parser.add_argument("--start", required=True, type=pandas.to_datetime)
    parser.add_argument("--type", default="era5land")
    parser.add_argument("--hres_ic", type="Path")
    parser.add_argument("--input_file_type", default="ic")
    
    args = parser.parse_args()
    # Convert the date/time to a formatted string
    t = args.start.strftime("%Y%m%dT%H%MZ")
    print(args.mask, args.file, t)
    # If necessary replace ERA5 land/surface fields with higher-resolution options
    if "era5land" in args.type:
        replace_landsurface_with_eraland_ic.swap_land_era5land(args.mask, args.file, t)
        shutil.move(args.file.as_posix(), args.file.as_posix().replace(".tmp", ""))
    elif "barra" in args.type:
        replace_landsurface_with_barra_ic.swap_land_barra(args.mask, args.file, t)
        shutil.move(args.file.as_posix(), args.file.as_posix().replace(".tmp", ""))
    elif "astart" in args.type:
        if "ic" in args.input_file_type:
            replace_landsurface_with_ff_ic.swap_land_ff(args.mask, args.file, args.hres_ic, t)
            shutil.move(args.file.as_posix(), args.file.as_posix().replace(".tmp", ""))
        else:
           print("No need to swap out IC") 
    else:
        print("No need to swap out IC")
if __name__ == "__main__":
    main()
