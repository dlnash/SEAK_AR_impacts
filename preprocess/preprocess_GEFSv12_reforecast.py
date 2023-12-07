######################################################################
# Filename:    preprocess_GEFSv12_reforecast.py
# Author:      Deanna Nash dnash@ucsd.edu
# Description: Script to take downloaded GEFSv12 reforecast u, v, and spfh data for each day, preprocess IVT data and save as single netCDF file
# https://registry.opendata.aws/noaa-gefs-reforecast/ (data link)
#
######################################################################

## import libraries
import os, sys
import yaml
import xarray as xr

path_to_repo = '/cw3e/mead/projects/cwp140/scratch/dnash/repos/SEAK_AR_impacts/'
sys.path.append(path_to_repo+'modules')
import GEFSv12_funcs as gefs

path_to_data = '/cw3e/mead/projects/cwp140/scratch/dnash/data/'

config_file = str(sys.argv[1]) # this is the config file name
job_info = str(sys.argv[2]) # this is the job name

config = yaml.load(open(config_file), Loader=yaml.SafeLoader) # read the file
job = config[job_info] # pull the job info from the dict

year = ddict['year']
date = ddict['date']
ens = ddict['ens']
varname = 'ivt' ## can be 'ivt', 'freezing_level', or 'prec'

print('Preprocessing IVT ....')
varname_lst = ['ugrd', 'vgrd', 'spfh']
ds_lst = []
for i, varname in enumerate(varname_lst):
    ds = gefs.read_and_regrid_prs_var(varname, date, year, ens, 'ivt')
    ds_lst.append(ds)

ds = xr.merge(ds_lst) # merge u, v, and q into single ds
ds = ds.sel(isobaricInhPa=slice(300, 1000))
ds = ds.reindex(isobaricInhPa=ds.isobaricInhPa[::-1])
ds_IVT = gefs.calc_IVT(ds) # calculate IVT

## save IVT data to netCDF file
print('Writing {0} to netCDF ....'.format(date))
out_fname = path_to_data + 'preprocessed/GEFSv12_reforecast/{0}/{1}_{0}.nc'.format(varname, date)
ds_IVT.to_netcdf(path=out_fname, mode = 'w', format='NETCDF4')