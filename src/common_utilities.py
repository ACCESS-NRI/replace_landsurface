# Copyright 2024 ACCESS-NRI (https://www.access-nri.org.au/)
# See the top-level COPYRIGHT.txt file for details.
#
# SPDX-License-Identifier: Apache-2.0
#
# Created by: Chermelle Engel <Chermelle.Engel@anu.edu.au>

import mule
import iris
import xarray as xr
import numpy as np

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

def replace_in_ff_problematic(f, mf_out, replace, stashcode, canopy_pixels, landsea_pixels):

    current_data = f.get_data()
    data=current_data.copy()

    if stashcode == 218:
        for j in range(len(canopy_pixels)):
            iy=canopy_pixels[j][0]
            ix=canopy_pixels[j][1]
            if np.isnan(data[iy,ix]):
                data[iy,ix]=1.
    elif stashcode == 33:
        for j in range(len(landsea_pixels)):
            data[landsea_pixels[j][0],landsea_pixels[j][1]]=0.

    mf_out.fields.append(replace([f, data]))

def problematic_pixels(infile):
    """
    Function to get locations of pixels that have incomplete canopy height information or 
    problematic land/sea definitions.

    Parameters
    ----------
    infile : string
        The name of the start dump file to read

    Returns
    -------
    2d numpy array
        A 2-D numpy array containg the field data for the date/time and spatial extent
    """

    # defining the variable names of surface altitude, soil porosity and canopy height in the start dump files
    var_altitude="surface_altitude"
    var_soil="soil_porosity"
    var_canopy="canopy_height"

    # Read in the relevant data
    # One single read of the relevant variables is faster than individual reads
    d = iris.load(infile,[var_altitude,var_soil,var_canopy])

    # Creating an orography mask and storing the latitude and longitude data for reporting purposes
    orog_data=xr.DataArray.from_iris(d[0])
    lats=orog_data['latitude'].data
    lons=orog_data['longitude'].data
    orog_mask=np.where(orog_data.data[:,:]>0.,1,0) 

    # Creating a soil parameter based mask
    soil_data=xr.DataArray.from_iris(d[1])
    soil_mask=np.where(np.isnan(soil_data.data[:,:]),1,0)

    # Creating a canopy mask - screening across all five different plant types
    canopy_data=xr.DataArray.from_iris(d[2])
    canopy_mask=np.where(np.isnan(canopy_data.data[:,:,:]),1,0)
    canopy_mask=np.sum(canopy_mask,axis=0)
    canopy_mask=np.where(canopy_mask>0,1,0)

    # Creating a compound mask that will indicate 1 for just canopy nan or 2 for canopy and soil nan
    compound_data=canopy_mask+soil_mask

    # Removing any sea points (points with altitude 0 or less
    compound_data=compound_data*orog_mask

    # Finding locations of problematic pixels in two sets
    # One for missing canopy alone and one for misclassified land
    try:
        canopy_pixels=np.argwhere(compound_data==1).compute()
        landsea_pixels=np.argwhere(compound_data==2).compute()
    except:
        canopy_pixels=np.argwhere(compound_data==1)
        landsea_pixels=np.argwhere(compound_data==1)

    # Printing information to the standard output for reporting purposes (so scientists can be aware)
    npoints,nxy = (canopy_pixels.shape)
    if npoints>0:
        for i in range(npoints):
            print("%.1f, %.1f, Nan canopy"%(lons[canopy_pixels[i,1]],lats[canopy_pixels[i,0]]))

    npoints,nxy = (landsea_pixels.shape)
    if npoints>0:
        for i in range(npoints):
            print("%.1f, %.1f, Misplaced Orography"%(lons[landsea_pixels[i,1]],lats[landsea_pixels[i,0]]))

    # returning pixel locations so they can be processed appropriately
    return canopy_pixels,landsea_pixels

