"""
Filename:    preprocess_SEAK-WRF_2Dvar.py
Author:      Deanna Nash, dlnash@ucsb.edu
Description: preprocess daily variables from 40 years of SEAK-WRF data and save as yearly nc files
"""

## Imports
import os, sys
import glob
import numpy as np
import xarray as xr

# Necessary to add cwd to path when script run
# by SLURM (since it executes a copy)
sys.path.append(os.getcwd())

# Path to modules
sys.path.append('../modules')
# Import my modules
from wrf_preprocess import preprocess_2Dvar, preprocess_UVwind

## Set up paths
path_to_wrf = '/expanse/lustre/scratch/dnash/temp_project/downloaded/WRF/' # access raw SEAK-WRF files
path_to_out = '/home/dnash/DATA/preprocessed/' # save preprocessed precip

# command for selecting variables **include XTIME,XLONG,XLAT in var list
# ncks -v varname1,varname2 input_file output_file

### Input ###

### Variable to Process ###
# output_varname = 'PCPT' # precip
# output_varname = 'T2' # 2M Temperature
output_varname = 'SNOW' # Snow Water Equivalent
# output_varname = 'UV' # uv wind
# levlst = ['1000', '925', '850'] # hPa


### START PROGRAM ###
start_yr = 1980
end_yr = 2019

## Loop through all above years
for year in np.arange(start_yr, end_yr+1):
    print('Processing ...', year)
    
    # get list of filenames that contain data from that year from current year folder
    filenames = []
    for name in glob.glob(path_to_wrf + 'WRFDS_{0}-*.nc'.format(str(year))):
        filenames.append(name)
    # sort filenames so they are in chronological order
    filenames = sorted(filenames)
    print(len(filenames))
    ## create new ds with just precip
    print('Reading', output_varname)
    if output_varname == 'UV':
        ds = preprocess_UVwind(filenames, levlst)
    else:
        ds = preprocess_2Dvar(filenames, output_varname, temp_resolution='daily')
    
    # write to netCDF
    print('Writing', output_varname, ' to netCDF')
    fname = os.path.join(path_to_out, 'SEAK-WRF-{0}/WRFDS_{0}_{1}.nc').format(output_varname, str(year))
    ds.to_netcdf(path=fname, mode = 'w', format='NETCDF4')