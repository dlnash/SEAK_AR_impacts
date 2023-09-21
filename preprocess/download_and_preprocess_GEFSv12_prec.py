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
# import dask
from dask.distributed import progress # this gives us a nice progress bar
path_to_repo = '/cw3e/mead/projects/cwp140/scratch/dnash/repos/SEAK_AR_impacts/'
sys.path.append(path_to_repo+'modules')
import GEFSv12_funcs as gefs

## set up paths
path_to_out  = path_to_repo + 'out/'       # output files (numerical results, intermediate datafiles) -- read & write
path_to_figs = path_to_repo +'figs/'      # figures
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
ARIDs = duration_df['trackID']
start_dates = duration_df['start_date']
end_dates = duration_df['end_date']


def process_GEFSv12_prec(ARID, start_date, end_date):
    print('Processing .... AR ID {0}'.format(ARID))
    ## for each AR event between 2000 and 2019, create a list of dates to download GEFSv2 data
    new_start = start_date - timedelta(days=7)
    date_lst = pd.date_range(new_start, end_date, freq='1D')
    
    ## need year and date values for finding files on S3 bucket
    year = date_lst.strftime("%Y").values
    date = date_lst.strftime("%Y%m%d").values
    
    ## save list of years and list of dates as text files in out
    np.savetxt(path_to_repo +r'out/prec/{0}_yrlst.txt'.format(ARID), year, fmt='%s')
    np.savetxt(path_to_repo +r'out/prec/{0}_datelst.txt'.format(ARID), date, fmt='%s')
    
    ## run download_GEFSv12_reforecast.sh to download IVT data to folder named 'ARID'
    ## run bash script to download files for AR event
    bash_script = path_to_repo +"downloads/download_GEFSv12_reforecast.sh"
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
    bash_script = path_to_repo +"downloads/clean_GEFSv12_reforecast.sh"
    print(subprocess.run([bash_script, ARID, 'prec']))
    
    return out_fname


## run one at a time
# results = []
# for index, row in duration_df.iterrows():
#     z = process_GEFSv12_prec(row)
#     results.append(z)

# dask.compute(results)
client = sys.argv[1]
futures = client.map(process_GEFSv12_prec, ARIDs, start_dates, end_dates)
progress(futures) # this will show us progress of our function running over time