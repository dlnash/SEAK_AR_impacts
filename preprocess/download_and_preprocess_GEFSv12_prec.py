######################################################################
# Filename:    download_and_preprocess_GEFSv12_prec.py
# Author:      Deanna Nash dnash@ucsd.edu
# Description: Script to download GEFSv12 reforecast precipitation data for each AR event, preprocess the data and save as single netCDF file
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
complete_trackID = gefs.list_of_processed_trackIDs('prec')

## read AR duration file
duration_df = pd.read_csv(path_to_out + 'AR_track_duration_SEAK.csv')
duration_df['start_date'] = pd.to_datetime(duration_df['start_date'])
duration_df['end_date'] = pd.to_datetime(duration_df['end_date'])
duration_df.index = duration_df['start_date']
## keep only rows where we haven't preprocessed the dates yet
idx = ~duration_df['trackID'].isin(complete_trackID)
duration_df = duration_df[idx]

@dask.delayed
def process_GEFSv12_prec(row):
    ARID = str(int(row['trackID']))
    print('Processing .... AR ID {0}, Index {1}'.format(ARID, index))
    ## for each AR event between 2000 and 2019, create a list of dates to download GEFSv2 data
    new_start = row['start_date'] - timedelta(days=7)
    date_lst = pd.date_range(new_start, row['end_date'], freq='1D')
    
    ## need year and date values for finding files on S3 bucket
    year = date_lst.strftime("%Y").values
    date = date_lst.strftime("%Y%m%d").values
    
    ## save list of years and list of dates as text files in out
    np.savetxt(r'../out/prec/{0}_yrlst.txt'.format(ARID), year, fmt='%s')
    np.savetxt(r'../out/prec/{0}_datelst.txt'.format(ARID), date, fmt='%s')
    
    ## run download_GEFSv12_reforecast.sh to download IVT data to folder named 'ARID'
    ## run bash script to download files for AR event
    bash_script = "../downloads/download_GEFSv12_reforecast.sh"
    print(subprocess.run([bash_script, ARID, 'prec']))
    
    ## preprocess precipitation data to single xarray ds for each AR event
    ## 7 days before AR makes landfall to end of AR event
    print('Preprocessing precipitation ....')
    prec = gefs.read_sfc_var('apcp', 'tp', ARID)

    ## save precipitation data to netCDF file
    print('Writing {0} to netCDF ....'.format(ARID))
    out_fname = path_to_data + 'preprocessed/GEFSv12_reforecast/prec/{0}_prec.nc'.format(ARID)
    prec.to_netcdf(path=out_fname, mode = 'w', format='NETCDF4')
    
    ## delete original downloaded data - run another clean-up bash file
    bash_script = "../downloads/clean_GEFSv12_reforecast.sh"
    print(subprocess.run([bash_script, ARID, 'prec']))
    
    return out_fname

results = []
for index, row in duration_df.iterrows():
    z = process_GEFSv12_prec(row)
    results.append(z)

dask.compute(results)