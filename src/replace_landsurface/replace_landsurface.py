# Copyright 2024 ACCESS-NRI (https://www.access-nri.org.au/)
# See the top-level COPYRIGHT.txt file for details.
#
# SPDX-License-Identifier: Apache-2.0
#
# Created by: Chermelle Engel <Chermelle.Engel@anu.edu.au>

"""
Replace the land-surface fields in the astart file with higher-resolution data
"""
#TODO: delete after testing
# barra_fname='/g/data/vk83/testing/data/replace_landsurface/integration_tests/driving_data/etc/barra_r2/1hr/ts/latest/ts_AUS-11_ERA5_historical_hres_BOM_BARRA-R2_v1_1hr_202008-202008.nc'
# fname='/g/data/tm70/cbe563/test_replace_land_surface/BARRAR2/GAL9_astart'
# mask='/scratch/tm70/cbe563/cylc-run/u-dg767.b/share/data/ancils/Lismore/d1100/qrparm.mask'
# date='202008090320'
#TODO: delete after testing

import argparse
import shutil
from pathlib import Path

from replace_landsurface import (
    replace_landsurface_with_BARRA2R_IC,
    replace_landsurface_with_ERA5land_IC,
    replace_landsurface_with_FF_IC,
)

def main():

    """
    Calls the command line argument parser and process the arguments using the right function.

    Parameters
    ----------
    None
    The arguments are given via the command-line

    Returns
    -------
    None
    An output file is written
    """ 

    # Parse the command-line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', required=True, type=Path)
    parser.add_argument('--start', required=True, type=str, help="A date in the format 'YYYYmmddHHMM'.")
    parser.add_argument('--type', default="era5land")
    parser.add_argument('--hres_ic', type=Path)
    args = parser.parse_args()

    # If necessary replace ERA5 land/surface fields with higher-resolution options
    if "era5land" in args.type:
        replace_landsurface_with_ERA5land_IC.swap_land_era5land(args.file, args.start)
        shutil.move(args.file.as_posix(), args.file.as_posix().replace('.tmp', ''))
    elif "barra" in args.type:
        replace_landsurface_with_BARRA2R_IC.swap_land_barra(args.file, args.start)
        shutil.move(args.file.as_posix(), args.file.as_posix().replace('.tmp', ''))
    elif "astart" in args.type:
        replace_landsurface_with_FF_IC.swap_land_ff(args.file, args.hres_ic, args.start)
        shutil.move(args.file.as_posix(), args.file.as_posix().replace('.tmp', ''))
    else:
        print("No need to swap out IC")

if __name__ == '__main__':
    main()

