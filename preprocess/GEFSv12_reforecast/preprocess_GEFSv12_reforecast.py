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
import numpy as np
import shutil

path_to_repo = '/home/dnash/repos/SEAK_AR_impacts/'
sys.path.append(path_to_repo+'modules')
import GEFSv12_funcs as gefs

config_file = str(sys.argv[1]) # this is the config file name
job_info = str(sys.argv[2]) # this is the job name

config = yaml.load(open(config_file), Loader=yaml.SafeLoader) # read the file
ddict = config[job_info] # pull the job info from the dict

year = ddict['year']
date = ddict['date']
variable = 'freezing_level' ## can be 'ivt', 'freezing_level', or 'uv1000'

for i, st in enumerate(range(0, 80, 8)):
    print(st, st+8)
    start = st
    stop = st+8
    
    if variable == 'ivt':
        print('Loading u, v, and q data ....')
        varname_lst = ['ugrd', 'vgrd', 'spfh']
        ds_lst = []
        for i, varname in enumerate(varname_lst):
            ds = gefs.read_and_regrid_prs_var(varname, date, year, start, stop)
            ds_lst.append(ds)
        
        ## load in surface pressure
        print('Loading surface pressure data ....')
        ds_pres = gefs.read_sfc_var('pres_sfc', date, year, start, stop)
        ds_lst.append(ds_pres)
        
        ds = xr.merge(ds_lst) # merge u, v, and q into single ds
        ds = ds.sel(isobaricInhPa=slice(300, 1000))
        ds = ds.reindex(isobaricInhPa=ds.isobaricInhPa[::-1])
        
        ## mask values below surface pressure
        print('Masking values below surface ....')
        varlst = ['q', 'u', 'v']
        for i, varname in enumerate(varlst):
            ds[varname] = ds[varname].where(ds[varname].isobaricInhPa < ds.sp/100., drop=False)
        
        ## integrate to calculate IVT
        print('Calculating IVT ....')
        ds_IVT = gefs.calc_IVT_manual(ds) # calculate IVT
        ds_IVT = ds_IVT.isel(step=slice(0, 8)) # confirm that it only is 8 time steps
        ds = ds_IVT

    if variable == 'uv1000':
        print('Loading u and v data ....')
        varname_lst = ['ugrd_pres', 'vgrd_pres']
        ds_lst = []
        
        for i, varname in enumerate(varname_lst):
            ds = gefs.read_sfc_var(varname, date, year, start, stop)
            ds = ds.sel(isobaricInhPa=1000.)
            ds_lst.append(ds)
            
        ds = xr.merge(ds_lst) # merge u and v into single ds

    if variable == 'freezing_level':
        print('Loading tmp and hgt data ....')
        varname_lst = ['tmp', 'hgt']
        ds_lst = []
        for i, varname in enumerate(varname_lst):
            ds = gefs.read_and_regrid_prs_var(varname, date, year, start, stop)
            ds_lst.append(ds)

        ds = xr.merge(ds_lst) # merge tmp and hgt data
        ds = ds.sel(isobaricInhPa=slice(1000, 200)) ## only interested in freezing level below 200 hPa
        ds = gefs.calc_freezing_level(ds) # calculate freezing level (m)


#### NOW SAVE FILE #### 
    # get info for saving file
    start = ds.step.values[0].astype('timedelta64[h]')
    stop = ds.step.values[-1].astype('timedelta64[h]')
    start = int(start / np.timedelta64(1, 'h'))
    stop = int(stop / np.timedelta64(1, 'h'))

    ## save data to netCDF file
    print('Writing {0} to netCDF ....'.format(date))
    path_to_data = '/expanse/lustre/scratch/dnash/temp_project/mclimate/{0}/'.format(variable)
    fname = '{0}_{3}_F{1}_F{2}.nc'.format(date, start, stop, variable) 
    ds.load().to_netcdf(path=path_to_data + fname, mode = 'w', format='NETCDF4')


    ### COPY FROM LUSTRE TO MAIN SPACE
    path_to_final_data = '/expanse/nfs/cw3e/cwp140/preprocessed/GEFSv12_reforecast/{0}/'.format(variable)
    print('Copying preprocessed data...')
    inname = path_to_data + fname
    outname = path_to_final_data + fname
    print('... {0} to {1}'.format(inname, outname))
    shutil.copy(inname, outname) # copy file over to data folder
