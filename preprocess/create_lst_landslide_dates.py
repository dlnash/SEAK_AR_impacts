######################################################################
# Filename:    create_lst_landslide_dates.py
# Author:      Deanna Nash dnash@ucsd.edu
# Description: Script to create .csv of unique landslide dates to compare M-Climate values and create historical maps for
#
######################################################################

# Standard Python modules
import os, sys
import glob
import numpy as np
import pandas as pd
import xarray as xr
from datetime import datetime, timedelta
sys.path.append('../modules')
import globalvars
path_to_data = globalvars.path_to_data
path_to_out  = '../out/'       # output files (numerical results, intermediate datafiles) -- read & write

#####################################################
### LANDSLIDE DATES FROM USGS NEWSWORTHY DATABASE ###
#####################################################
fname = path_to_data + 'downloads/SEAK_News_Reported_Landslides.csv'
df = pd.read_csv(fname)
df = df.set_index(pd.to_datetime(df['Day_min']))
## subset to dates between 2000 and 2024
idx = (df.index >= '2000-01-01') & (df.index <= '2024-12-31')
df = df.loc[idx]
print(len(df))
## get unique dates - these are the impact dates
unique_dates2 = df.index.unique()
unique_dates2 = unique_dates2.sort_values()
len(unique_dates2)

###################################################
### LANDSLIDE DATES FROM NOAA STORM EVENTS DATA ###
###################################################
## glob files in directory since they have weird names
fname_pattern = path_to_data + 'downloads/noaastormevents/StormEvents_details-ftp_v1.0_d20*.csv'
fname_lst = glob.glob(fname_pattern, recursive=False)
df_lst = []
for i, fname in enumerate(sorted(fname_lst)):
    print(fname)
    df = pd.read_csv(fname, header=0)
    ## subset to Juneau WFO
    idx = (df.WFO == 'AJK')
    df = df.loc[idx]

    ## debris flow specific
    idx = df['EVENT_TYPE'] == 'Debris Flow'
    deb_flow = df.loc[idx]
    ## filter by keywords
    idx = (df['EVENT_NARRATIVE'].str.contains('mudslide')) | \
          (df['EVENT_NARRATIVE'].str.contains('debris flow')) | \
          (df['EVENT_NARRATIVE'].str.contains('landslide')) | \
          (df['EVENT_NARRATIVE'].str.contains('mass wasting')) | \
          (df['EPISODE_NARRATIVE'].str.contains('mudslide')) | \
          (df['EPISODE_NARRATIVE'].str.contains('debris flow')) | \
          (df['EPISODE_NARRATIVE'].str.contains('landslide')) | \
          (df['EPISODE_NARRATIVE'].str.contains('mass wasting'))
        
    df = df.loc[idx]
    df_lst.append(df)
    df_lst.append(deb_flow)

df = pd.concat(df_lst)
# ## set begin date to index
# Convert 'YearMonth' to datetime and extract year and month
df['YearMonth'] = pd.to_datetime(df['BEGIN_YEARMONTH'], format='%Y%m')
df['Year'] = df['YearMonth'].dt.year
df['Month'] = df['YearMonth'].dt.month
df['Day'] = pd.to_datetime(df['BEGIN_DAY'], format='%d').dt.day

# Create datetime column
df['DateTime'] = pd.to_datetime(df[['Year', 'Month', 'Day']])
df = df.set_index(pd.to_datetime(df['DateTime']))
# ## subset to start_date and end_date
idx = (df.index >= '2000-01-01') & (df.index <= '2024-12-31')
df = df.loc[idx]
print(len(df))
## get unique list of dates
unique_dates3 = df.index.unique()
unique_dates3 = unique_dates3.sort_values()
print(len(unique_dates3))

## COMBINE NEWSWORTHY LANDSLIDE DATES WITH NOAA STORM EVENTS DATES
combined_dt_array = np.concatenate((unique_dates2.values, unique_dates3.values))
d = {'dates': combined_dt_array}
dates = pd.DataFrame(d)
## add special date (there was landslide activity on this day)
new_row = pd.DataFrame([{'dates': pd.to_datetime('2005-11-23', format='%Y-%m-%d')}])
## add special date for paper (this is NOT A LANDSLIDE DATE)
new_row1 = pd.DataFrame([{'dates': pd.to_datetime('2024-09-23', format='%Y-%m-%d')}])
new_row2 = pd.DataFrame([{'dates': pd.to_datetime('2025-08-08', format='%Y-%m-%d')}])
dates = pd.concat([dates, new_row, new_row1, new_row2], ignore_index=True)
final_dates_lst = dates['dates'].unique()


## create list of init dates we need 
## we will run mclimate based on these dates and lead times
## for each impact date
## for initialization date 1-7 days before impact date
## F000, F024, F072, ...
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

varname_lst = ['impact_date', 'init_date']
for i, varname in enumerate(varname_lst):
    # Convert string to datetime objects (assuming format is YYYY-MM-DD)
    df[varname] = pd.to_datetime(df[varname])

    # Format datetime objects to a different string format (e.g., YYYYMMDD)
    df[varname] = df[varname].dt.strftime('%Y%m%d')

out_fname = path_to_out + 'landslide_dates.csv'
df.to_csv(out_fname, index=False)

## subset to GEFS archive dates for download script
df = df.set_index(pd.to_datetime(df['init_date'], format='%Y%m%d'))

# subset to 2020-2024
idx = (df.index >= '2020-01-01') & (df.index <= '2024-12-31')
tmp = df.loc[idx]

# Save as CSV
tmp.to_csv(path_to_out+'GEFS_dates_download.csv', index=False)


##################################################################
### CREATE A LIST OF DATES WHEN THERE IS NO REPORTED LANDSLIDE ###
##################################################################
# Range start and end
start_date = datetime(2000, 1, 1)
end_date = datetime(2019, 12, 31)

# Convert existing dates to a set of just date parts for comparison
existing_date_set = set(d.date() for d in final_dates_lst)

# Generate all dates in the range
current_date = start_date
all_dates_in_range = []
while current_date <= end_date:
    all_dates_in_range.append(current_date.date())
    current_date += timedelta(days=1)

# Filter dates that are NOT in existing_date_set
missing_dates = [d for d in all_dates_in_range if d not in existing_date_set]
print('Number of days where there is no reported landslides: {0}'.format(len(missing_dates)))

d = {'init_date': pd.to_datetime(missing_dates, format='%Y%m%d')}
df = pd.DataFrame(d)

out_fname = path_to_out + 'non-landslide_dates.csv'
df.to_csv(out_fname, index=False)
