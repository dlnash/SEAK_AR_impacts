######################################################################
# Filename:    concat_mclimate.py
# Author:      Deanna Nash dnash@ucsd.edu
# Description: Script to concat mclimate files for GEFSv12 Reforecast into dayofyear files
#
######################################################################

## import libraries
import os, sys
import yaml
import xarray as xr
import glob
import pandas as pd

path_to_data = '/expanse/nfs/cw3e/cwp140/'     # project data -- read only
varname = 'prec'

config_file = str(sys.argv[1]) # this is the config file name
job_info = str(sys.argv[2]) # this is the job name

config = yaml.load(open(config_file), Loader=yaml.SafeLoader) # read the file
ddict = config[job_info] # pull the job info from the dict

mon = ddict['month']
day = ddict['day']

# ## get list of filenames on project space
# fname_pattern = os.path.join(path_to_data, 'preprocessed/mclimate/GEFSv12_reforecast_mclimate_{2}_{0}{1}_*hr-lead.nc').format(mon, day, varname)
## get list of files on scratch space
fname_pattern = '/expanse/lustre/scratch/dnash/temp_project/{2}_mclimate/GEFSv12_reforecast_mclimate_{2}_{0}{1}_*hr-lead.nc'.format(mon, day, varname)
filenames = glob.glob(fname_pattern)

print(len(filenames))
ds = xr.open_mfdataset(filenames)

# ## out path for project space
# fname = path_to_data + 'preprocessed/{2}_mclimate/GEFSv12_reforecast_mclimate_{2}_{0}{1}.nc'.format(mon.zfill(2), day.zfill(2), varname)

## out path for scratch space
fname = '/expanse/lustre/scratch/dnash/temp_project/{2}_mclimate_concat/GEFSv12_reforecast_mclimate_{2}_{0}{1}.nc'.format(mon.zfill(2), day.zfill(2), varname)
print(fname)
ds.to_netcdf(path=fname, mode = 'w', format='NETCDF4')