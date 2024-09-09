######################################################################
# Filename:    preprocess_GEFS.py
# Author:      Deanna Nash dnash@ucsd.edu
# Description: Script to take downloaded GEFS u, v, rh, and t data for each given init date and lead time, 
# preprocess IVT data and save as single netCDF file, extract and save freezing level data
#
######################################################################

## import libraries
import os, sys
import yaml
import xarray as xr
import numpy as np
import pandas as pd

path_to_repo = '/home/dnash/repos/SEAK_AR_impacts/'
sys.path.append(path_to_repo+'modules')
import GEFS_funcs as gefs

config_file = str(sys.argv[1]) # this is the config file name
job_info = str(sys.argv[2]) # this is the job name

config = yaml.load(open(config_file), Loader=yaml.SafeLoader) # read the file
ddict = config[job_info] # pull the job info from the dict

init_date = ddict['init_date']
F = ddict['F']

path_to_data = '/expanse/lustre/scratch/dnash/temp_project/downloaded/GEFS/{0}/'.format(init_date)

## dictionary of variables we need
gfs_vardict = {
"u_wind":{"typeOfLevel":'isobaricInhPa',"shortName":"u"}, #U-component of wind
"v_wind":{"typeOfLevel":'isobaricInhPa',"shortName":"v"}, #V-component of wind
"temperature":{"typeOfLevel":'isobaricInhPa',"shortName":"t"}, #Temperature
"rh":{"typeOfLevel":'isobaricInhPa',"shortName":"r"}, #Relative Humidity
"sfc_pressure":{'name': 'Surface pressure', 'typeOfLevel': 'surface', 'level': 0, 'paramId': 134, 'shortName': 'sp'}, #surface pressure
"freezing_level": {'typeOfLevel': 'isothermZero', 'shortName': 'gh'} ## freezing level 
}
######################
### COMPUTE UV1000 ###
######################
## open all pressure variables needed for IVT calculation
varname_lst = ['u_wind', 'v_wind']
ds_lst = []
for i, varname in enumerate(varname_lst):
    ds = gefs.read_GEFS_pres_grb(F, gfs_vardict[varname], path_to_data)
    ds_lst.append(ds)

## merge variable datasets into single dataset
ds = xr.merge(ds_lst)

## select the 1000 hPa level
ds = ds.sel(isobaricInhPa=1000)

## save data to netCDF file
print('Writing {0} to netCDF ....'.format('UV1000'))
path_to_out = '/expanse/nfs/cw3e/cwp140/preprocessed/GEFS/GEFS/'
out_fname = path_to_out + '{0}.t00z.0p50.f{1}.{2}'.format(init_date, F, 'UV1000')
ds.to_netcdf(path=out_fname, mode = 'w', format='NETCDF4')

###################
### COMPUTE IVT ###
###################

print('Reading pressure level data ....')
## open pgrb2a surface pressure data
fname = path_to_data + 'geavg.t00z.pgrb2a.0p50.f{0}'.format(F)
sfc = xr.open_dataset(fname, engine='cfgrib',filter_by_keys=gfs_vardict['sfc_pressure'])

## open all pressure variables needed for IVT calculation
varname_lst = ['u_wind', 'v_wind', 'rh', 'temperature']
ds_lst = [sfc]
for i, varname in enumerate(varname_lst):
    ds = gefs.read_GEFS_pres_grb(F, gfs_vardict[varname], path_to_data)
    ds_lst.append(ds)

## merge variable datasets into single dataset
ds = xr.merge(ds_lst)

## Compute specific humidity from relative humidity and temperature
print('Computing specific humidity ....')
#extending pressure vector to 3d array to match rh shape
pressure_3d = np.tile(ds["r"].isobaricInhPa.values[:, np.newaxis, np.newaxis], (1, ds["r"].values.shape[1], ds["r"].values.shape[2]))

q = gefs.specific_humidity(temperature=ds["t"].values, pressure=pressure_3d*100, relative_humidity=ds["r"].values/100)

## put into dataarray and add to dataset
q = xr.DataArray(q, name="q", dims=( "isobaricInhPa", "latitude","longitude"), 
                 coords={"latitude": ds.latitude.values, "longitude":ds.longitude.values,
                        "isobaricInhPa": ds.isobaricInhPa.values})
ds['q'] = q

## drop t and rh since we don't need them anymore
ds = ds.drop_vars(['t', 'r'])

## mask values below surface pressure
print('Masking values below surface ....')
varlst = ['q', 'u', 'v']
for i, varname in enumerate(varlst):
    ds[varname] = ds[varname].where(ds[varname].isobaricInhPa < ds.sp/100., drop=False)

## integrate to calculate IVT
print('Calculating IVT ....')
ds_IVT = gefs.calc_IVT_manual(ds) # calculate IVT

## save data to netCDF file
print('Writing {0} to netCDF ....'.format('IVT'))
path_to_out = '/expanse/lustre/scratch/dnash/temp_project/preprocessed/GEFS/'
out_fname = path_to_out + '{0}.t00z.0p50.f{1}.{2}'.format(init_date, F, 'IVT')
ds_IVT.to_netcdf(path=out_fname, mode = 'w', format='NETCDF4')

##############################
### COMPUTE FREEZING LEVEL ###
##############################

## extract freezing level data
freezing_level_ds = gefs.read_GEFS_pgrb2b(F, gfs_vardict['freezing_level'], path_to_data)

## save data to netCDF file
print('Writing {0} to netCDF ....'.format('Freezing Level'))
path_to_out = '/expanse/lustre/scratch/dnash/temp_project/preprocessed/GEFS/'
out_fname = path_to_out + '{0}.t00z.0p50.f{1}.{2}'.format(init_date, F, 'freezing_level')
freezing_level_ds.to_netcdf(path=out_fname, mode = 'w', format='NETCDF4')