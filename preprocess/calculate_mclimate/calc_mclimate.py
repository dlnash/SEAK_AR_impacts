######################################################################
# Filename:    calc_mclimate.py
# Author:      Deanna Nash dnash@ucsd.edu
# Description: Script to calculate mclimate for GEFSv12 Reforecast
#
######################################################################

## import libraries
import os, sys
import yaml
import xarray as xr
import pandas as pd
import numpy as np
import metpy.calc as mpcalc
from metpy.units import units
import dask
from datetime import timedelta

dask.config.set(**{'array.slicing.split_large_chunks': True})
path_to_data = '/cw3e/mead/projects/cwp140/scratch/dnash/data/'      # project data -- read only

config_file = str(sys.argv[1]) # this is the config file name
job_info = str(sys.argv[2]) # this is the job name

config = yaml.load(open(config_file), Loader=yaml.SafeLoader) # read the file
ddict = config[job_info] # pull the job info from the dict

F = int(ddict['F'])
mon = int(ddict['month'])
day = int(ddict['day'])

def get_filename_GEFSv12_reforecast(F):
    ## this is the number of hours of lead time
    ## for getting the correct filename
    
    # F = int((np.timedelta64(ndays, 'D')+np.timedelta64(nhours, 'h'))/np.timedelta64(1, 'h'))
    ## the F-lead that the files are saved as
    li = [3, 24, 27, 48, 51, 72, 75, 96, 99, 120, 123, 144, 147, 168, 171, 192, 195, 216, 219, 240]
    
    for idx in range(len(li)-1):
        if li[idx] < F <= li[idx+1]:
            pos1, pos2 = idx, idx+1

    return li[pos1], li[pos2]


## for each year between 2000 and 2019
date_lst = []
for i, yr in enumerate(range(2000, 2020)):
    ## get 45 days before date
    center_date = '{0}-{1}-{2}'.format(yr, mon, day)
    center_date = pd.to_datetime(center_date)
    start_date = center_date - timedelta(days=45)
    
    ## get 45 days after November 21
    end_date = center_date + timedelta(days=45)

    ## make a list of dates between start_date and end_date
    dates = pd.date_range(start_date, end_date, freq='1D')
    
    date_lst.append(dates)
    
## concatenate all years together into single list    
final_lst = np.concatenate(date_lst)
## remove dates outside GEFSv12 Reforecast
idx = (pd.DatetimeIndex(final_lst).year < 2020) & (pd.DatetimeIndex(final_lst).year >= 2000)
final_lst = final_lst[idx]

print(start_date, end_date)

## load all days from the new subset
## create list of fnames
fname_lst = []
path_to_data = '/data/projects/Comet/cwp140/'
path_to_data = '/cw3e/mead/projects/cwp140/scratch/dnash/data/'
varname = 'ivt'

## append filenames to a list
print('Gathering filenames ...')
for i, dt in enumerate(final_lst):
    ts = pd.to_datetime(str(dt)) 
    d = ts.strftime("%Y%m%d")
    F1, F2 = get_filename_GEFSv12_reforecast(F)
    fname = path_to_data + 'preprocessed/GEFSv12_reforecast/{0}/{1}_{0}_F{2}_F{3}.nc'.format(varname, d, F1, F2)
    fname_lst.append(fname)

### Read the dataset
print('Reading the data ...')
### Select the xx hr lead time step
## this is the index value for selecting the timestep in the dataset
idx = np.timedelta64(int(np.timedelta64(F, 'h')/np.timedelta64(1, 'ns')), 'ns')

def preprocess(ds):
    ds = ds.drop_vars(["ivtu", "ivtv"])
    ds = ds.sel(step=idx) # select the 24 hr lead step
    
    return ds

## use xr.open_mfdataset to read all the files within that ssn clim
ds = xr.open_mfdataset(fname_lst, concat_dim="valid_time", combine="nested", engine='netcdf4', chunks={"lat": 100, "lon": 100}, preprocess=preprocess)

print('Calculating quantiles...')
## need to rechunk so time is a single chunk
ds = ds.chunk(dict(valid_time=-1))

# Percentile will be a set range of percentiles including <90th, then every 0.1 until 100th/MAX
# I might add 75th-90th, and < 75th
a = np.array([0, .75, .9])
b = np.arange(.91, 1.001, 0.01)
quantile_arr = np.concatenate((a, b), axis=0)

## Calculate the percentiles
ivt_mclimate = ds.quantile(quantile_arr, dim=['valid_time', 'number'], skipna=True)

## add dayofyear and lead to coordinates
ivt_mclimate = ivt_mclimate.assign_coords(step=F)
ivt_mclimate = ivt_mclimate.expand_dims('step')
period = pd.Period("2023-{0}-{1}".format(mon, day), freq='H')
ivt_mclimate = ivt_mclimate.assign_coords(dayofyear=period.day_of_year)
ivt_mclimate = ivt_mclimate.expand_dims('dayofyear')
ivt_mclimate

# write to netCDF
fname = os.path.join(path_to_data, 'preprocessed/mclimate/GEFSv12_reforecast_mclimate_ivt_{0}{1}_{2}hr-lead.nc'.format(mon, day, F))
ivt_mclimate.load().to_netcdf(path=fname, mode = 'w', format='NETCDF4')