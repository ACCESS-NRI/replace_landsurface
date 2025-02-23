# Copyright 2024 ACCESS-NRI (https://www.access-nri.org.au/)
# See the top-level COPYRIGHT.txt file for details.
#
# SPDX-License-Identifier: Apache-2.0
#
# Initially created by: Chermelle Engel <Chermelle.Engel@anu.edu.au>

import os
import warnings
from glob import glob
from collections import namedtuple
from pathlib import Path

import mule
import numpy as np
import xarray as xr

TEMPORARY_SUFFIX = ".tmp"
DECIMAL_PRECISION = 4
ROSE_DATA = os.environ.get("ROSE_DATA", "")

STASH_SOIL_MOISTURE = 9
STASH_SOIL_TEMPERATURE = 20
STASH_SURFACE_TEMPERATURE = 24
STASH_LAND_MASK = 30

BoundingBox = namedtuple("BoundingBox", ("latmin", "latmax", "lonmin", "lonmax"))


class ReplaceOperator(mule.DataOperator):
    """
    Mule operator for replacing the data of a field.
    By default, the operator will leave the original field unchanged and return a new field as a copy of the original, with the new data.
    Set 'in_place=True' to replace the data of the original field instead (a reference to the field will still be returned).
    """
    def __init__(self, in_place: bool = False) -> None:
        self.in_place = in_place

    def new_field(self, sources: tuple[mule.Field,np.ndarray]) -> mule.Field:
        source_field = sources[0]
        new_field = source_field if self.in_place else source_field.copy()
        return new_field

    def transform(self, sources: tuple[mule.Field,np.ndarray], result) -> np.ndarray:
        new_data = sources[1]
        return new_data


def get_bounding_box(mule_file: mule.UMFile) -> BoundingBox:
    """Get spatial extent information for the replacement.

    Parameters
    ----------
    mule_file : mule.UMFile object
        Input UM fields file to be replaced

    Returns
    -------
    BoundingBox
        The BoundingBox namedtuple containing the spatial extent of the input file
    """
    # Get extent from the land mask (stash 30) if present, otherwise use the first field
    # We don't use the fields file extent because sometimes it is not correct
    try:
        field = [f for f in mule_file.fields if f.lbuser4 == STASH_LAND_MASK][0]
    except IndexError:
        field = mule_file.fields[0]
    # Get the latitude extent
    dlat = field.bdy
    nlat = mule_file.integer_constants.num_rows
    latmin = round(
        field.bzy + dlat, DECIMAL_PRECISION
    )  # rounded to avoid numerical inaccuracy
    latmax = round(
        latmin + (nlat - 1) * dlat, DECIMAL_PRECISION
    )  # rounded to avoid numerical inaccuracy

    # Get the latitude extent
    dlon = field.bdx
    nlon = mule_file.integer_constants.num_cols
    lonmin = round(
        field.bzx + dlon, DECIMAL_PRECISION
    )  # rounded to avoid numerical inaccuracy
    lonmax = round(
        lonmin + (nlon - 1) * dlon, DECIMAL_PRECISION
    )  # rounded to avoid numerical inaccuracy

    return BoundingBox(latmin, latmax, lonmin, lonmax)


def get_latitude_name(file: xr.Dataset | xr.DataArray) -> str:
    """
    Get the name of the latitude coordinate in the file ('lat' or 'latitude').

    Parameters
    ----------
    file : xarray.Dataset or xarray.DataArray
        The xarray Dataset or DataArray to get the latitude name from.

    Returns
    -------
    string
        The name of the latitude coordinate.
    """
    if "latitude" in file.coords:
        return "latitude"
    elif "lat" in file.coords:
        return "lat"
    else:
        raise ValueError("The latitude coordinate name could not be understood.")


def get_longitude_name(file: xr.Dataset | xr.DataArray) -> str:
    """
    Get the name of the longitude coordinate in the file ('lon' or 'longitude').

    Parameters
    ----------
    file : xarray.Dataset or xarray.DataArray
        The xarray Dataset or DataArray to get the longitude name from.

    Returns
    -------
    string
        The name of the longitude coordinate.
    """
    if "longitude" in file.coords:
        return "longitude"
    elif "lon" in file.coords:
        return "lon"
    else:
        raise ValueError("The longitude coordinate name could not be understood.")


def get_hres_data(
    fname: str,
    var_name: str,
    date: str,
    bounds: BoundingBox,
    depth_index: int | None = None,
) -> np.ndarray:
    """
    Get the high-resolution data from the data_source file.
    based on the var_name variable.

    Parameters
    ----------
    fname : string
        The name of the high-resolution file to get data from.
    var_name : string
        The variable name to get data from.
    date : string
        The date in the format "YYYYmmddHHMM".
    bounds : BoundingBox
        BoundingBox namedtuple containing the spatial extent to retrieve the data.
    depth_index : int
        The index of the vertical depth dimension.

    Returns
    -------
    numpy.ndarray
        A numpy array containg the data for the date/time and spatial extent
    """

    # Open the file containing the data
    if Path(fname).exists():
        data = xr.open_dataset(fname)
    else:
        raise FileNotFoundError(f"File '{fname}' not found.")
    # Select the variable
    try:
        data = data[var_name]
    except KeyError:
        raise ValueError(
            f"Variable '{var_name}' not found in high-resolution file '{fname}'."
        )

    latitude_name = get_latitude_name(data)
    longitude_name = get_longitude_name(data)

    # If needed, modify data so it has the same structure as UM files: ascending latitudes (-90 to 90) and positive longitudes (0 to 360)
    # Guarantee ascending latitude
    if data[latitude_name][0] > data[latitude_name][1]:  # descending latitude
        data = data.reindex(
            {latitude_name: data[latitude_name][::-1]}
        )  # flip the latitude

    # Guarantee positive longitudes
    if any(data[longitude_name] < 0):  # negative longitude (-180 to 180)
        longitude = data[longitude_name]
        new_index = [lon for lon in longitude if lon >= 0] + [
            lon for lon in longitude if lon < 0
        ]  # move negative longitudes to the end
        data = data.reindex({longitude_name: new_index})
        new_longitude = [
            lon if lon >= 0 else (360 + lon) for lon in new_index
        ]  # turn longitudes into (0 to 360) structure
        data = data.assign_coords({longitude_name: new_longitude})

    # Select the date
    try:
        data = data.sel(time=date)
    except KeyError:
        # If the exact date is not found select the nearest date and send a warning message
        data = data.sel(time=date, method="nearest")
        actual_date = (
            data.time.values.astype("datetime64[m]").tolist().strftime("%Y%m%d%H%M")
        )
        warnings.warn(
            f"The date '{date}' was not found in the high-resolution file '{fname}'.\n"
            f"Using the nearest date '{actual_date}' instead."
        )

    # Select the horizontal spatial extent
    data = data.sel({
        latitude_name: slice(bounds.latmin, bounds.latmax),
        longitude_name: slice(bounds.lonmin, bounds.lonmax),
    })

    # Select the vertical depth if needed
    if depth_index is not None:
        data = data.isel({'depth': depth_index})
    return data.data

def get_new_data(
    field: mule.Field,
    fname: str,
    var_name: str,
    date: str,
    bounds: BoundingBox,
    multiplier: float = 1,
    depth_index: int | None = None,
) -> np.ndarray:
    """
    Get the new high-resolution data for the replacement.



    Returns
    -------
    new_data : numpy.ndarray
        A numpy array containing the new data.
    """
    current_data = field.get_data()
    data = get_hres_data(fname, var_name, date, bounds, depth_index)
    data = data * multiplier
    # If data is missing, keep the original data
    new_data = np.where(np.isnan(data), current_data, data)
    return new_data

def get_era5land_fname(var_name: str, date: str):
    ERA_DIR = os.path.join(ROSE_DATA, "etc", "era5_land")
    year = date[0:4]
    month = date[4:6]
    indir = os.path.join(ERA_DIR, var_name, year)
    try:
        fname = glob(os.path.join(indir, f'*_{year}{month}??-{year}{month}??.nc'))[0]
    except IndexError:
        raise FileNotFoundError(f"No ERA5-Land file found in '{indir}' for date '{date}'.")
    return fname

def get_barra_fname(var_name: str, frequency: str, date: str):
    BARRA_DIR = os.path.join(ROSE_DATA, "etc", "barra_r2")
    year = date[0:4]
    month = date[4:6]
    indir = os.path.join(BARRA_DIR, frequency, var_name, 'latest')
    try:
        fname = glob(os.path.join(indir, f'*_{year}{month}-{year}{month}.nc'))[0]
    except IndexError:
        raise FileNotFoundError(f"No BARRA-R2 file found in '{indir}' for date '{date}'.")
    return fname

def swap_land_era5land(
    mf_in: mule.UMFile,
    date: str,
    replace_operator: ReplaceOperator,
    bounds: BoundingBox,
) -> mule.UMFile:
    """
    Replace the input file with the high-resolution era5-land data.

    Parameters
    ----------
    mf_in : mule.UMFile
        The input file with the coarser resolution data to be replaced with the high-resolution one.
    date : string
        The requested date for the high-resolution data, in the format "YYYYmmddHHMM".
    replace_operator : ReplaceOperator
        The Mule operator for replacing the data.
    bounds : BoundingBox
        The spatial extent for the replacement.
    
    Returns
    -------
    mf_out : mule.UMFile.
        The output mule UMFile containing the updated data.
    """
    # The depths of soil for the conversion
    SOIL_MULTIPLIERS = (100.0, 250.0, 650.0, 2000.0)

    mf_out = mf_in.copy(include_fields=True)
   
    # For each field in the input write to the output file (but modify as required)
    for indf,field in enumerate(mf_in.fields):
        lblev = field.lblev
        stash = field.lbuser4
        if stash in (STASH_SOIL_MOISTURE, STASH_SOIL_TEMPERATURE, STASH_SURFACE_TEMPERATURE):
            if field.lbuser4 == STASH_SOIL_MOISTURE:
                var_name = "swvl" + str(lblev)
                multiplier = SOIL_MULTIPLIERS[lblev - 1]
            elif field.lbuser4 == STASH_SOIL_TEMPERATURE:
                var_name = "stl" + str(lblev)
                multiplier = 1
            elif field.lbuser4 == STASH_SURFACE_TEMPERATURE:
                var_name = "skt"
                multiplier = 1
            fname = get_era5land_fname(var_name, date)
            new_data = get_new_data(field, fname, var_name, date, bounds, multiplier)
            mf_out.fields[indf] = replace_operator((field, new_data))
    return mf_out

def swap_land_barra(
    mf_in: mule.UMFile,
    date: str,
    replace_operator: ReplaceOperator,
    bounds: BoundingBox,
) -> mule.UMFile:
    """
    Replace the input file with the high-resolution barra data.

    Parameters
    ----------
    mf_in : mule.UMFile
        The input file with the coarser resolution data to be replaced with the high-resolution one.
    date : string
        The requested date for the high-resolution data, in the format "YYYYmmddHHMM".
    replace_operator : ReplaceOperator
        The Mule operator for replacing the data.
    bounds : BoundingBox
        The spatial extent for the replacement.
    
    Returns
    -------
    mf_out : mule.UMFile.
        The output mule UMFile containing the updated data.
    """

    mf_out = mf_in.copy(include_fields=True)

    # For each field in the input write to the output file (but modify as required)
    for indf,field in enumerate(mf_in.fields):
        lblev = field.lblev
        stash = field.lbuser4
        if stash in (STASH_SOIL_MOISTURE, STASH_SOIL_TEMPERATURE, STASH_SURFACE_TEMPERATURE):
            if field.lbuser4 == STASH_SOIL_MOISTURE:
                var_name = "mrsol"
                frequency = "3hr"
                depth_index = lblev - 1
            elif field.lbuser4 == STASH_SOIL_TEMPERATURE:
                var_name = "tsl"
                frequency = "3hr"
                depth_index = lblev - 1
            elif field.lbuser4 == STASH_SURFACE_TEMPERATURE:
                var_name = "ts"
                frequency = "1hr"
                depth_index = None
            fname = get_barra_fname(var_name, frequency, date)
            new_data = get_new_data(field, fname, var_name, date, bounds, depth_index=depth_index)
            mf_out.fields[indf] = replace_operator((field, new_data))
    return mf_out

def swap_land(fname: Path, date: str, source_data_type: str) -> None:
    """
    Replace the input file with the high-resolution data.

    Parameters
    ----------
    fname : string
        Path to the input file with the coarser resolution data to be replaced with the high-resolution one.
    date : string
        The requested date for the high-resolution data, in the format "YYYYmmddHHMM".
    source_data_type : string
        The source data type. Can be one among: ('era5land', 'barra').

    Returns
    -------
    None.
        A new file is written, overwriting the input fname.
    """
    
    # Input filepath
    ff_in = fname.as_posix()
    # Output temporary filepath
    ff_out_tmp = ff_in + TEMPORARY_SUFFIX
    
    # Read the input file
    mf_in = mule.load_umfile(ff_in)
    
    # Get the spatial extent for the replacement
    bounds = get_bounding_box(mf_in)

    # Create a Mule Replacement Operator
    replace_op = ReplaceOperator()

    if source_data_type == "era5land":
        swap_land_function = swap_land_era5land
    elif source_data_type == "barra":
        swap_land_function = swap_land_barra
    else:
        raise ValueError(f"Unsupported source_data_type: {source_data_type}")

    mf_out = swap_land_function(mf_in, date, replace_op, bounds)
    # Write output file
    mf_out.validate = lambda *args, **kwargs: True
    mf_out.to_file(ff_out_tmp)
    # Replace original input file with temporary output file
    os.rename(ff_out_tmp, ff_in)
    