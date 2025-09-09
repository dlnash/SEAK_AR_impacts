"""
Filename:    create_box_whisker_csv.py
Author:      Deanna Nash, dnash@ucsd.edu
Description: For the landslide dates and non-landslide dates, create a .csv file with the maximum percentile rank for all the variables
"""

# Standard Python modules
import os, sys
import glob
import numpy as np
import pandas as pd
import xarray as xr
sys.path.append('../modules')
from timeseries import select_months
import globalvars

## set paths
path_to_data = globalvars.path_to_data
path_to_out  = '../out/'       # output files (numerical results, intermediate datafiles) -- read & write

##############################
### FUNCTION FOR DATAFRAME ###
##############################

def create_df_from_init_dates(df):
    IVT_lst = []
    Z0_lst = []
    UV_lst = []
    QPF_lst = []
    AR_index_lst = []
    for index, row in df.iterrows():
        ## read csv files from landslide dates
        model_name = row['model_name']
        F = row['F']
        
        fdate = row['init_date'].strftime("%Y%m%d")
        impact_date = row['impact_date'].strftime("%Y-%m-%d")
        try:
            ## for each row, open the file using the init date
            fname = path_to_data+'mclimate_csv/mclimate_init{0}.csv'.format(fdate)
            test = pd.read_csv(fname)
            test["valid_time"] = row['init_date'] + pd.to_timedelta((test.index + 1) * 6, unit="h")
            test = test.set_index(pd.to_datetime(test['valid_time']))
            ## then subset to impact date
            subset = test.loc[impact_date]
            
            ## pull the maximum values for each var
            IVT_lst.append(subset['IVT'].max())
            Z0_lst.append(subset['Freezing Level'].max())
            UV_lst.append(subset['UV'].max())
            QPF_lst.append(subset['QPF'].max())
            AR_index_lst.append(subset['AR_index'].max())
        except FileNotFoundError:
            print('Skipping {0}, data not available...'.format(fdate))
            ## set vals to nan
            IVT_lst.append(np.nan)
            Z0_lst.append(np.nan)
            UV_lst.append(np.nan)
            QPF_lst.append(np.nan)
            AR_index_lst.append(np.nan)
            
    
    df['IVT'] = IVT_lst
    df['Z0'] = Z0_lst
    df['UV'] = UV_lst
    df['QPF'] = QPF_lst
    df['AR_index'] = AR_index_lst
    
    return df

###################################
### COMPUTE FOR LANDSLIDE DATES ###
###################################

## read unique landslide dates
df = pd.read_csv('../out/landslide_dates.csv')
df['impact_date'] = pd.to_datetime(df['impact_date'], format="%Y%m%d")
df['init_date'] = pd.to_datetime(df['init_date'], format="%Y%m%d")

df = create_df_from_init_dates(df)
df.to_csv(path_to_out+'landslide_box-whisker.csv', index=False) # Save as CSV

#######################################
### COMPUTE FOR NON-LANDSLIDE DATES ###
#######################################
## read non-landslide dates
df = pd.read_csv('../out/non-landslide_dates.csv')
df = df.set_index(pd.to_datetime(df['init_date'], format='%Y-%m-%d'))
final_dates_lst = df.index

date_lst = []
impact_date_lst = []
model_lst = []
F_lst = []
for i, date in enumerate(final_dates_lst):
    ## skip 2 events - 20200227, 20200817
    ## the data from GEFS was too hard to download for these dates
    if (date.strftime("%Y%m%d") == '20200227') | (date.strftime("%Y%m%d") == '20200817'):
        pass
    else:
        for j, init_lead in enumerate(np.arange(1, 8)):
            F_lst.append(init_lead*24) # lead in hours
            init_date = date - pd.to_timedelta(init_lead, unit='D')
            date_lst.append(init_date)
            impact_date_lst.append(date)
            
            if init_date.year < 2020:
                model_name = 'GEFSv12_reforecast'
            else:
                model_name = 'GEFS_archive'
    
            model_lst.append(model_name)

d = {'impact_date': impact_date_lst, 'init_date': date_lst, 'model_name': model_lst, 'F': F_lst}
df = pd.DataFrame(d)

## cut the df so it takes out init dates before 2000-01-01
idx = (df['init_date'] >= '2000-01-01')
df = df.loc[idx]

df = create_df_from_init_dates(df)
df.to_csv(path_to_out+'non-landslide_box-whisker.csv', index=False) # Save as CSV