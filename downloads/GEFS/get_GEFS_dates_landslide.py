"""
Filename:    get_GEFS_dates_landslide.py
Author:      Deanna Nash, dnash@ucsd.edu
Description: Create a .csv file with a list of dates and lead times to download GEFS based on landslide dates.

"""

## import libraries
import os, sys
import numpy as np
import pandas as pd
import xarray as xr
import yaml

path_to_data = '/expanse/nfs/cw3e/cwp140/'
path_to_out  = '../../out/'       # output files (numerical results, intermediate datafiles) -- read & write

## load landslide data
fname = path_to_data + 'downloads/Landslide_Data.csv'
df = pd.read_csv(fname)
df = df.set_index(pd.to_datetime(df['Day_min']))

# subset to 2020-2024
idx = (df.index >= '2020-01-01') & (df.index <= '2024-12-31')
tmp = df.loc[idx]
unique_dates_GEFS = tmp.index.unique()

## create list of init dates we need for 2020-2023
## we will download and preprocess GEFS archive data
date_lst = []
F_lst = []
for i, date in enumerate(unique_dates_GEFS):
    for j, init_lead in enumerate(np.arange(0, 8)):
        init_date = date - pd.to_timedelta(init_lead, unit='D')
        F_lst.append(init_lead*24)
        date_lst.append(init_date)

d = {'d': date_lst, 'F': F_lst}
GEFS_df = pd.DataFrame(d)
GEFS_df = GEFS_df.set_index(pd.to_datetime(GEFS_df['d']))
GEFS_df

# Save as CSV
GEFS_df.to_csv(path_to_out+'GEFS_dates_download.csv', index=False)