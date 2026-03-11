######################################################################
# Filename:    get_AR_dates.py
# Author:      Deanna Nash dnash@ucsd.edu
# Description: Script to pull AR dates for NWS
#  records on the Atmospheric Rivers that have occurred in Southeast during Winter months since 2020 
# any storms between November & March, 2020 - current. 
#
######################################################################
# Standard Python modules
import os, sys
import glob
import numpy as np
import pandas as pd
import xarray as xr
from datetime import datetime, timedelta
sys.path.append('../modules')
from timeseries import select_months_ds
import globalvars
path_to_data = globalvars.path_to_data

### read AR data
ar_filename =  path_to_data + 'downloads/globalARcatalog_ERA5_1940-2024_v4.0.nc'
vars_needed = [
    "kidmap"
]

## Read data
ext = [-141., -130., 54, 60]
ds = xr.open_dataset(ar_filename, engine='netcdf4', decode_times=True)[vars_needed]
ds = ds.isel(lev=0, ens=0).squeeze()
ds = ds.assign_coords({"lon": (((ds.lon + 180) % 360) - 180)}) # Convert DataArray longitude coordinates from 0-359 to -180-179
ds = ds.sortby('lon')
da = ds.sel(lat=slice(ext[3], ext[2]), lon=slice(ext[0], ext[1])).kidmap.squeeze()

# subset to winter months between 2020 and 2024
idx = (ds.time.dt.year >= 2020)
da = da.sel(time=idx)
da = select_months_ds(da, 11, 3)
print(da)

ar_present = da.max(dim=["lat", "lon"])
# Find max, then make binary (True/False)
ARDT_binary = (ar_present > 0).astype(int)

df_dates = pd.DataFrame(
    {"time": ARDT_binary.time.values}
)

df_dates["AR_present"] = ARDT_binary.values

# Save as CSV
df_dates.to_csv('../out/tARgetv4_AR_dates_NDJFM_2020-2024_141W_130W_54N_60N.csv', index=False)