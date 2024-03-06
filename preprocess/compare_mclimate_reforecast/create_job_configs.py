######################################################################
# Filename:    create_job_configs.py
# Author:      Deanna Nash dnash@ucsd.edu
# Description: Script to create .yaml configuration file to run job_array with slurm for comparing M-Climate to GEFSv12 Reforecast Data
#
######################################################################

## import libraries
import pandas as pd
from datetime import timedelta
import numpy as np
import yaml
from itertools import chain

## get list of all AR days
fname = '../../out/SEAK_ardates_daily.csv'
ar_df = pd.read_csv(fname) # read in AR dates
idx = (ar_df.AR == 1)
ar_df = ar_df.loc[idx]
# reset the index as "time"
ar_df = ar_df.set_index(pd.to_datetime(ar_df['Unnamed: 0']))
## subset dates to Jan 2000 - Dec 2019
idx = (ar_df.index.year >= 2000) & (ar_df.index.year <= 2019)
ar_df = ar_df.loc[idx]
ar_dates = ar_df.index.values


dates_new = []
mon_lst = []
day_lst = []
for i, date in enumerate(ar_dates):
    ts = pd.to_datetime(str(date))
    # ts = date
    d = ts - timedelta(days=3) ## need to get the date of 3 days prior
    t = d.strftime('%Y%m%d')
    mon_lst.append(d.month)
    day_lst.append(d.day)
    dates_new.append(t)

jobcounter = 0
filecounter = 0
## loop through to create dictionary for each job
d_lst = []
dest_lst = []
njob_lst = []
for i, (date, mon, day) in enumerate(zip(dates_new, mon_lst, day_lst)):
    jobcounter += 1

    d = {'job_{0}'.format(jobcounter):
         {'month': mon,
          'day': day,
          'date': date
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
        call_string = "python compare_mclimate_reforecast.py config_{0}.yaml 'job_{1}'".format(i+1, j+1)
        call_str_lst.append(call_string)
        
    ## now write those lines to a text file
    with open('calls_{0}.txt'.format(i+1), 'w',encoding='utf-8') as f:
        for line in call_str_lst:
            f.write(line)
            f.write('\n')
        f.close()
