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

date = int(ddict['date']) # this is the AR date

F = 24 ## update this to whatever you are testing!!!

valid_time = pd.to_datetime(str(date)) # this is the AR date
d = valid_time - timedelta(hours=F) ## we want the initialization date to be x hours prior to AR date
mon = d.month # month of initialization
day = d.day # day of initialization
init_date = d.strftime('%Y%m%d')

## load the reforecast for the initialization date
fc = mclim_func.load_reforecast(init_date, 'ivt')
fc = fc.sel(step=F)

## load the mclimate for the same initialization date
mclimate = mclim_func.load_mclimate(mon, day)
mclimate = mclimate.sel(step=F)

## compare the mclimate to the reforecast
ds = mclim_func.compare_mclimate_to_forecast(fc, mclimate)

## add time to ds
ds = ds.assign_coords({"init_time": d, "valid_time": valid_time})

## save data to netCDF file
print('Writing to netCDF ....')
out_fname = path_to_data + 'preprocessed/mclimate_AR_dates/mclimate_ivt_{0}_F{1}.nc'.format(date, F)
ds.to_netcdf(path=out_fname, mode = 'w', format='NETCDF4')
