"""
Filename:    preprocess_database.py
Author:      Deanna Nash, dnash@ucsd.edu
Description: Preprocessing script to take GEFSv12 Reforecast Data, Mesowest Data, and Impact Database and combined into a pd dataframe for all available stations.
"""

## import libraries
import os, sys
import yaml
import xarray as xr
import pandas as pd
import numpy as np
import metpy.calc as mpcalc
from metpy.units import units

%matplotlib inline

sys.path.append('../modules')
import ar_funcs

path_to_data = '/cw3e/mead/projects/cwp140/scratch/dnash/data/'      # project data -- read only
path_to_out  = '../out/'       # output files (numerical results, intermediate datafiles) -- read & write
path_to_figs = '../figs/'      # figures

## read .yaml file with station information
yaml_doc = '../data/ASOS_station_info.yaml'
config = yaml.load(open(yaml_doc), Loader=yaml.SafeLoader)

## build empty dataframes
df_lst = []
prec_df_lst = []
for i, stationID in enumerate(config):
    print(i, stationID)
    df = ar_funcs.build_empty_df(stationID)
    df_lst.append(df)
    
    ## open mesowest files
    prec_df = ar_funcs.read_mesowest_prec_data(stationID)
    prec_df_lst.append(prec_df)
    
## read AR duration file
duration_df = pd.read_csv('../out/AR_track_duration_SEAK.csv')
# duration_df['start_date'] = pd.to_datetime(duration_df['start_date'])
duration_df['start_date'] = duration_df['trackID'].map(ar_funcs.get_new_start)
duration_df['end_date'] = pd.to_datetime(duration_df['end_date'])
duration_df.index = duration_df['trackID']

ARID_issues = [200411121210, 200411191202, 200610151213, 200610201812, 201205201201, 201209010004]


error_desc = ['IVT nan', 'IVT nan' ,'prec wrong dates', 'prec wrong dates', 'prec time unsorted', 'freeze level not same datetime as ivt']
duration_df = duration_df[~duration_df['trackID'].isin(ARID_issues)]

ARID_lst = duration_df.index.values


## enumerate through ARIDs
for i, ARID in enumerate(ARID_lst):
    ARID = int(ARID)
    ## open IVT file
    ds = ar_funcs.read_GEFSv12_reforecast_data('ivt', ARID)   
    ## get IVT information
    df_lst = ar_funcs.preprocess_IVT_info(config, ds, ARID, df_lst)
    ## close IVT file
    ds.close()
    
    ## open freezing level file
    ds = ar_funcs.read_GEFSv12_reforecast_data('freezing_level', ARID)
    ## get freezing level info
    ds_lst = ar_funcs.preprocess_freezing_level(config, ds, ARID, df_lst)    
    ## close freezing level file
    ds.close()
    
    ## open precipitation file
    ds = ar_funcs.read_GEFSv12_reforecast_data('prec', ARID)    
    ## get precipitation information
    df_lst = ar_funcs.preprocess_prec_GEFS(config, ds, ARID, df_lst)
    ## close precipitation file
    ds.close()
    
    ## pull mesowest precipitation data into dfs
    idx = (duration_df['trackID'] == ARID)
    start_date = duration_df.loc[idx]['start_date'].values[0]
    end_date = duration_df.loc[idx]['end_date'].values[0] + pd.Timedelta(hours=12)
    df_lst = ar_funcs.preprocess_mesowest_precip(ARID, prec_df_lst, df_lst, start_date, end_date)
    

## load impact database
impact_df = ar_funcs.clean_impact_data(start_date = '2000-01-01', end_date = '2019-08-31')

subset_df_lst = []
ar_impact_lst = []
for i, stationID in enumerate(config):
    print(i, stationID)
    subset_df, ar_impact = ar_funcs.add_impact_info(i, stationID)
    subset_df_lst.append(subset_df)
    ar_impact_lst.append(ar_impact)
    
    outfile = path_to_out + 'combined_df_{0}.csv'.format(stationID)
    subset_df.to_csv(outfile)