######################################################################
# Filename:    download_and_preprocess_GEFSv12_ivt.py
# Author:      Deanna Nash dnash@ucsd.edu
# Description: Script to download GEFSv12 reforecast u, v, and spfh data for each AR event, preprocess IVT data and save as single netCDF file
# https://registry.opendata.aws/noaa-gefs-reforecast/ (data link)
#
######################################################################

## import libraries
import os, sys
import subprocess
import numpy as np
import pandas as pd
from datetime import timedelta
import dask

sys.path.append('../modules')
import GEFSv12_funcs as gefs

## set up paths
path_to_out  = '../out/'       # output files (numerical results, intermediate datafiles) -- read & write
path_to_figs = '../figs/'      # figures
path_to_data = '/cw3e/mead/projects/cwp140/scratch/dnash/data/'      # project data -- read only

## pull filenames from preprocessed directory into a list of trackIDs
complete_trackID = gefs.list_of_processed_trackIDs('ivt')

## read AR duration file
duration_df = pd.read_csv(path_to_out + 'AR_track_duration_SEAK.csv')
duration_df['start_date'] = pd.to_datetime(duration_df['start_date'])
duration_df['end_date'] = pd.to_datetime(duration_df['end_date'])
duration_df.index = duration_df['start_date']
## keep only rows where we haven't preprocessed the dates yet
idx = ~duration_df['trackID'].isin(complete_trackIDs)
duration_df = duration_df[idx]

def process_GEFSv12_ivt(row):
    ARID = str(int(row['trackID']))
    print('Processing .... AR ID {0}'.format(ARID))
    ## for each AR event between 2000 and 2019, create a list of dates to download GEFSv2 data
    new_start = row['start_date'] - timedelta(days=7)
    date_lst = pd.date_range(new_start, row['end_date'], freq='1D')
    
    ## need year and date values for finding files on S3 bucket
    year = date_lst.strftime("%Y").values
    date = date_lst.strftime("%Y%m%d").values
    
    ## save list of years and list of dates as text files in out
    np.savetxt(r'../out/ivt/{0}_yrlst.txt'.format(ARID), year, fmt='%s')
    np.savetxt(r'../out/ivt/{0}_datelst.txt'.format(ARID), date, fmt='%s')
    
    ## run download_GEFSv12_reforecast.sh to download IVT data to folder named 'ARID'
    ## run bash script to download files for AR event
    bash_script = "../downloads/download_GEFSv12_reforecast.sh"
    print(subprocess.run([bash_script, ARID, 'ivt']))
    
    ## preprocess IVT data to single xarray ds for each AR event
    ## 7 days before AR makes landfall to end of AR event
    print('Preprocessing IVT ....')
    varname_lst = ['ugrd', 'vgrd', 'spfh']
    ds_lst = []
    for i, varname in enumerate(varname_lst):
        ds = gefs.read_and_regrid_prs_var(varname, ARID, date, year, 'ivt')
        ds_lst.append(ds)

    ds = xr.merge(ds_lst) # merge u, v, and q into single ds
    ds = ds.sel(isobaricInhPa=slice(300, 1000))
    ds = ds.reindex(isobaricInhPa=ds.isobaricInhPa[::-1])
    ds_IVT = gefs.calc_IVT(ds) # calculate IVT

    ## save IVT data to netCDF file
    print('Writing {0} to netCDF ....'.format(ARID))
    out_fname = path_to_data + 'preprocessed/GEFSv12_reforecast/ivt/{0}_ivt.nc'.format(ARID)
    ds_IVT.to_netcdf(path=out_fname, mode = 'w', format='NETCDF4')
    
    ## delete original downloaded data - run another clean-up bash file
    bash_script = "../downloads/clean_GEFSv12_reforecast.sh"
    print(subprocess.run([bash_script, ARID, 'ivt']))
    
    return out_fname

results = []
for index, row in duration_df.iterrows():
    z = process_GEFSv12_ivt(row)
    results.append(z)

dask.compute(results)