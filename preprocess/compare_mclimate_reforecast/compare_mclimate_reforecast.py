######################################################################
# Filename:    compare_mclimate_reforecast.py
# Author:      Deanna Nash dnash@ucsd.edu
# Description: Script to take the GEFSv12 mClimate and reforecast data and compare for a specific lead time and date
#
######################################################################

## import libraries
import os, sys
import yaml
import xarray as xr
import pandas as pd
from datetime import timedelta

path_to_repo = '/home/dnash/repos/SEAK_AR_impacts/'
sys.path.append(path_to_repo+'modules')
import mclimate_funcs as mclim_func

# dask.config.set(**{'array.slicing.split_large_chunks': True})
path_to_data = '/expanse/nfs/cw3e/cwp140/'     # project data -- read only

config_file = str(sys.argv[1]) # this is the config file name
job_info = str(sys.argv[2]) # this is the job name

config = yaml.load(open(config_file), Loader=yaml.SafeLoader) # read the file
ddict = config[job_info] # pull the job info from the dict

date = int(ddict['date'])
mon = int(ddict['month'])
day = int(ddict['day'])

## load the reforecast
fc = mclim_func.load_reforecast(date, 'ivt')

## load the mclimate for the same date
mclimate = mclim_func.load_mclimate(mon, day)

## compare the mclimate to the reforecast
ds = mclim_func.compare_mclimate_to_forecast(fc, mclimate)

## add time to ds
init_time = pd.to_datetime(date, format='%Y%m%d') # init date
valid_time = init_time + timedelta(days=3) ## the date in the config file is the init_time
ds = ds.assign_coords({"init_time": init_time, "valid_time": valid_time})

## save data to netCDF file
print('Writing to netCDF ....')
out_fname = path_to_data + 'preprocessed/mclimate_AR_dates/mclimate_ivt_{0}_F72.nc'.format(date)
ds.to_netcdf(path=out_fname, mode = 'w', format='NETCDF4')
