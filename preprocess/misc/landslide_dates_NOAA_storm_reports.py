# Standard Python modules
import os, sys
import glob
import numpy as np
import pandas as pd

## glob files in directory since they have weird names
path_to_data = '/expanse/nfs/cw3e/cwp140/'
fname_pattern = path_to_data + 'downloads/noaastormevents/StormEvents_details-ftp_*.csv'
fname_lst = glob.glob(fname_pattern, recursive=False)
df_lst = []
for i, fname in enumerate(sorted(fname_lst)):
    print(fname)
    df = pd.read_csv(fname, header=0)
    ## subset to Juneau WFO or CA 
    idx = (df.WFO == 'AJK') | (df.STATE == 'CA')
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
idx = (df.index >= '2023-10-01') & (df.index <= '2024-03-31')
df = df.loc[idx]