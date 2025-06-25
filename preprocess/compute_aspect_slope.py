"""
Filename:    compute_slope_aspect.py
Author:      Deanna Nash, dnash@ucsd.edu
Description: For GEFSv12 reforecast, compute the slope and aspect using the orography and save as intermediate netCDF.
"""

import os
import sys
import xarray as xr
import numpy as np
import richdem as rd

path_to_out  = '../out/'       # output files (numerical results, intermediate datafiles) -- read & write

ext = [-179.5, -110., 10., 70.]

fname = '/expanse/nfs/cw3e/cwp140/downloads/GEFSv12_reforecast/hgt_sfc_2000100100_c00.grib2'
ds = xr.open_dataset(fname, engine='cfgrib')
ds = ds.assign_coords({"longitude": (((ds.longitude + 180) % 360) - 180)}) # Convert DataArray longitude coordinates from 0-359 to -180-179
ds = ds.isel(step=1)
ds = ds.reindex(latitude=list(reversed(ds.latitude)))
ds = ds.sel(longitude=slice(ext[0], ext[1]), latitude=slice(ext[2], ext[3]))

## load the data into rich dem
rda = rd.rdarray(ds.orog.values, no_data=np.nan)
## calculate the slope
slope = rd.TerrainAttribute(rda, attrib='slope_riserun')
aspect = rd.TerrainAttribute(rda, attrib='aspect')

data = {
    "slope": (["lat", "lon"], slope),
    "aspect": (["lat", "lon"], aspect)
}

coords = {
    "lat": ds.latitude.values,
    "lon": ds.longitude.values
}

ds = xr.Dataset(data, coords=coords)

## write to netcdf
out_fname = '/expanse/nfs/cw3e/cwp140/preprocessed/GEFSv12_reforecast/GEFSv12_slope_aspect.nc'
ds.to_netcdf(out_fname, format="NETCDF4")