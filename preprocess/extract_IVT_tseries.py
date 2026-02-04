"""
Filename:    extract_IVT_tseries.py
Author:      Deanna Nash, dnash@ucsd.edu
Description: Script to read ERA5 IVT for one grid cell and save as csv.
"""
import os, sys
import xarray as xr
import glob
import pandas as pd
import numpy as np

path_to_data = '/cw3e/mead/projects/cwp162/data/preprocessed/ARScale_ERA5/'
fname_pattern = path_to_data + 'ERA5_ARScale_*.nc'
filenames = sorted(glob.glob(fname_pattern))
## 56.5N 132.5W OR 59N 135.5W
lat = 59.
lon = -135.5
df_lst = []
for i, fname in enumerate(filenames):
    print(fname)
    ds = xr.open_dataset(fname)
    ds = ds.sel(lat=lat, lon=lon)
    df = ds['IVT'].to_dataframe()
    df_lst.append(df)

df = pd.concat(df_lst)
df.to_csv('../out/IVT_ERA5_{0}N_{1}W.csv'.format(lat, lon*-1))