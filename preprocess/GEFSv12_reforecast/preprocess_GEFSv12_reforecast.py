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
ddict = config[job_info] # pull the job info from the dict

year = ddict['year']
date = ddict['date']
variable = 'ivt' ## can be 'ivt', 'freezing_level', or 'prec'

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
        ds_pres = gefs.read_sfc_var('pres', date, year, start, stop)
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
    
        # get info for saving file
        start = ds_IVT.step.values[0].astype('timedelta64[h]')
        stop = ds_IVT.step.values[-1].astype('timedelta64[h]')
        start = int(start / np.timedelta64(1, 'h'))
        stop = int(stop / np.timedelta64(1, 'h'))
    
        ## save IVT data to netCDF file
        print('Writing {0} to netCDF ....'.format(date))
        out_fname = path_to_data + 'preprocessed/GEFSv12_reforecast/ivt/{0}_ivt_F{1}_F{2}.nc'.format(date, start, stop) 
        ds_IVT.load().to_netcdf(path=out_fname, mode = 'w', format='NETCDF4')