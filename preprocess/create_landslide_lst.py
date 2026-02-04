######################################################################
# Filename:    create_landslide_lst.py
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
import pytz
sys.path.append('../modules')
import globalvars
path_to_data = globalvars.path_to_data
path_to_out  = '../out/'       # output files (numerical results, intermediate datafiles) -- read & write

########################
### HELPER FUNCTIONS ###
########################

def expand_date_ranges(df, start_col, end_col):
    """
    Expand each row into daily dates between start_col and end_col (inclusive)
    and return a unique, sorted DatetimeIndex.
    """
    all_dates = []

    for start, end in zip(df[start_col], df[end_col]):
        if pd.isna(start):
            continue
        if pd.isna(end):
            end = start  # assume single-day event if end missing

        dates = pd.date_range(start=start, end=end, freq='D')
        all_dates.append(dates)

    if not all_dates:
        return pd.DatetimeIndex([])

    return pd.DatetimeIndex(np.unique(np.concatenate(all_dates)))

cz_tz_map = {
    'EST': 'America/New_York',
    'EDT': 'America/New_York',
    'CST': 'America/Chicago',
    'CDT': 'America/Chicago',
    'MST': 'America/Denver',
    'MDT': 'America/Denver',
    'PST': 'America/Los_Angeles',
    'PDT': 'America/Los_Angeles',
    'AST': 'America/Anchorage',
    'ADT': 'America/Anchorage',
    'HST': 'Pacific/Honolulu'
}

def local_to_utc(row, col):
    tz_str = cz_tz_map.get(row['CZ_TIMEZONE'], None)
    if tz_str is None or pd.isna(row[col]):
        return pd.NaT

    return (
        row[col]
        .tz_localize(tz_str, ambiguous='NaT', nonexistent='NaT')
        .tz_convert('UTC')
    )


#####################################################
### LANDSLIDE DATES FROM USGS NEWSWORTHY DATABASE ###
#####################################################
fname = path_to_data + 'downloads/SEAK_News_Reported_Landslides.csv'
df = pd.read_csv(fname)

# Parse dates
ak_tz = pytz.timezone("America/Anchorage")
df['Day_min'] = pd.to_datetime(df['Day_min'], format='%m/%d/%y', errors='coerce')
df['Day_max'] = pd.to_datetime(df['Day_max'], format='%m/%d/%y', errors='coerce')


# Fill missing times
df['Time_min'] = df['Time_min'].fillna('12:00 AM')
df['Time_max'] = df['Time_max'].fillna('11:59 PM')

# Combine date + time (12-hour clock with AM/PM)
df['dt_min_local'] = pd.to_datetime(
    df['Day_min'].dt.strftime('%Y-%m-%d') + ' ' + df['Time_min'],
    format='%Y-%m-%d %I:%M %p',
    errors='coerce'
)

df['dt_max_local'] = pd.to_datetime(
    df['Day_max'].dt.strftime('%Y-%m-%d') + ' ' + df['Time_max'],
    format='%Y-%m-%d %I:%M %p',
    errors='coerce'
)
# Localize to Alaska time → UTC
df['dt_min_utc'] = (
    df['dt_min_local']
    .dt.tz_localize(ak_tz, ambiguous='NaT', nonexistent='NaT')
    .dt.tz_convert('UTC')
)

df['dt_max_utc'] = (
    df['dt_max_local']
    .dt.tz_localize(ak_tz, ambiguous='NaT', nonexistent='NaT')
    .dt.tz_convert('UTC')
)

# Subset to analysis window
idx = (df['dt_min_utc'] <= '2024-12-31') & (df['dt_max_utc'] >= '2000-01-01')
df = df.loc[idx]
print(len(df))
print(df[['Day_min', 'Time_min', 'dt_min_local', 'dt_min_utc']].head())
print(df[['Day_max', 'Time_max', 'dt_max_local', 'dt_max_utc']].head())

# Expand to daily dates
unique_dates2 = expand_date_ranges(df, 'dt_min_utc', 'dt_max_utc')
print(len(unique_dates2))

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

df = pd.concat(df_lst, ignore_index=True)
print(df[['BEGIN_DATE_TIME', 'CZ_TIMEZONE']].head())

# Parse begin/end datetimes
df['BEGIN_DATE_TIME'] = pd.to_datetime(
    df['BEGIN_DATE_TIME'],
    format='%d-%b-%y %H:%M:%S',
    errors='coerce'
)

df['END_DATE_TIME'] = pd.to_datetime(
    df['END_DATE_TIME'],
    format='%d-%b-%y %H:%M:%S',
    errors='coerce'
)

# If END is missing, treat as single-day event
df['END_DATE_TIME'] = df['END_DATE_TIME'].fillna(df['BEGIN_DATE_TIME'])

df['dt_min_utc'] = df.apply(local_to_utc, axis=1, col='BEGIN_DATE_TIME')
df['dt_max_utc'] = df.apply(local_to_utc, axis=1, col='END_DATE_TIME')


# Subset to analysis window
idx = (df['dt_min_utc'] <= '2024-12-31') & (df['dt_max_utc'] >= '2000-01-01')
df = df.loc[idx]

print(len(df))

print(df[['BEGIN_DATE_TIME', 'dt_min_utc', 'CZ_TIMEZONE']].head())

assert df['dt_min_utc'].dt.year.min() >= 1950
assert df['dt_min_utc'].dt.year.max() <= 2026

# Expand to daily dates
unique_dates3 = expand_date_ranges(df, 'dt_min_utc', 'dt_max_utc')
print(len(unique_dates3))

combined_dates = pd.DatetimeIndex(
    np.unique(np.concatenate([unique_dates2.values, unique_dates3.values]))
)

# Add special dates
extra_dates = pd.to_datetime([
    # '2005-11-23',  # known landslide activity
    '2024-09-23',  # paper-only date
])

final_dates_lst = (
    pd.to_datetime(
        np.concatenate([combined_dates.values, extra_dates.values]),
        utc=True
    )
    .normalize()      # snap to 00 UTC
    .unique()         # dedupe AFTER normalization
    .sort_values()
)


print(len(final_dates_lst))



####################################
### Connect dates to AR database ###
####################################

### read AR data
ar_filename =  path_to_data + 'downloads/globalARcatalog_ERA5_1940-2024_v4.0.nc'
vars_needed = [
    "kidmap"
]

## Read data
ext = [-141., -130., 54, 60]
ds = xr.open_dataset(ar_filename, engine='netcdf4', decode_times=True)[vars_needed]
ds = ds.isel(lev=0, ens=0).squeeze()
ds = ds.assign_coords({"lon": (((ds.lon + 180) % 360) - 180)}) # Convert DataArray longitude coordinates from 0-359 to -180-179
ds = ds.sortby('lon')
da = ds.sel(lat=slice(ext[3], ext[2]), lon=slice(ext[0], ext[1])).kidmap.squeeze()
da = da.assign_coords(
    time=pd.to_datetime(da.time.values).tz_localize(None)
)

## select dates from list
# final_dates_lst: DatetimeIndex, UTC, normalized to 00:00
six_hour_offsets = pd.to_timedelta([0, 6, 12, 18], unit='h')

six_hourly_dates = (
    final_dates_lst
    .repeat(len(six_hour_offsets))
    + np.tile(six_hour_offsets, len(final_dates_lst))
)

six_hourly_dates = six_hourly_dates.sort_values()

# Convert to a list of strings in 'YYYY-MM-DD' format
date_strings_list = six_hourly_dates.strftime('%Y-%m-%d').tolist()
# subset to landslide dates
da_ls = da.sel(time=date_strings_list)

# any AR at any time, any lat/lon on that day
ar_present = (
    da_ls
    .groupby("time.date")
    .max(dim=["time", "lat", "lon"])
)
# Find max, then make binary (True/False)
ARDT_binary = (ar_present > 0).astype(int)

df_dates = pd.DataFrame(
    {"date": final_dates_lst}
)

df_dates["AR_present"] = ARDT_binary.values
print(sum(ARDT_binary.values))
# Save as CSV
df_dates.to_csv(path_to_out+'landslide_dates_UTC.csv', index=False)

df_dates = df_dates.loc[df_dates.AR_present == 1]
final_dates_lst = pd.to_datetime(df_dates.date.values)

print(final_dates_lst)
print(len(final_dates_lst))

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

