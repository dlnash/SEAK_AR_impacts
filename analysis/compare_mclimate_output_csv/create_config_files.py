######################################################################
# Filename:    create_job_configs.py
# Author:      Deanna Nash dnash@ucsd.edu
# Description: Script to create .yaml configuration file to run job_array with slurm for comparing mclimate to reforecast for high impact dates
#
######################################################################

## import libraries
import pandas as pd
import numpy as np
import yaml
from itertools import chain

# ## read unique landslide dates from csv
# df = pd.read_csv('../../out/landslide_dates.csv')

dates = pd.date_range(start='2000-01-01', end='2019-12-31')

## now add the dates after 2020 - since we did not want to download and preprocess 4 years of GEFS, we just have the initialization dates needed
df = pd.read_csv('../../out/GEFS_dates_download.csv')
df = df.set_index(pd.to_datetime(df['init_date'], format='%Y%m%d'))
unique_dates2 = df.index.unique()

combined_dt_array = np.concatenate((dates.values, unique_dates2.values))

# make dataframe
combined_df = pd.DataFrame({'date': combined_dt_array})

# assign model name based on date
cutoff = pd.Timestamp('2020-01-01')
combined_df['model'] = np.where(
    combined_df['date'] < cutoff,
    'GEFSv12_reforecast',
    'GEFS_archive'
)

# optional: sort by date if needed
combined_df = combined_df.sort_values('date').reset_index(drop=True)

jobcounter = 0
filecounter = 0
## loop through to create dictionary for each job
d_lst = []
dest_lst = []
njob_lst = []

for index, row in combined_df.iterrows():
    jobcounter += 1
    
    d = {"job_{0}".format(jobcounter):
         {"init_date": row.date.strftime("%Y%m%d"),
          "model_name": row.model
          }}
    d_lst.append(d)
    
    if (jobcounter == 999):
        filecounter += 1
        ## merge all the dictionaries to one
        dest = dict(chain.from_iterable(map(dict.items, d_lst)))
        njob_lst.append(len(d_lst))
        ## write to .yaml file and close
        file=open("config_{0}.yaml".format(str(filecounter)),"w")
        yaml.dump(dest,file, allow_unicode=True, default_flow_style=None)
        file.close()
        
        ## reset jobcounter and d_lst
        jobcounter = 0
        d_lst = []
        
## now save the final config
filecounter += 1
## merge all the dictionaries to one
dest = dict(chain.from_iterable(map(dict.items, d_lst)))
njob_lst.append(len(d_lst))
## write to .yaml file and close
file=open("config_{0}.yaml".format(str(filecounter)),"w")
yaml.dump(dest,file, allow_unicode=True, default_flow_style=None)
file.close()

## create calls.txt for config_1(-8)

for i, njobs in enumerate(njob_lst):
    call_str_lst = []
    for j, job in enumerate(range(1, njobs+1, 1)):
        call_string = "python compare_mclimate_forecast.py config_{0}.yaml 'job_{1}'".format(i+1, j+1)
        call_str_lst.append(call_string)
        
    ## now write those lines to a text file
    with open('calls_{0}.txt'.format(i+1), 'w',encoding='utf-8') as f:
        for line in call_str_lst:
            f.write(line)
            f.write('\n')
        f.close()