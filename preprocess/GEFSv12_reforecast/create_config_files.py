######################################################################
# Filename:    create_job_configs.py
# Author:      Deanna Nash dnash@ucsd.edu
# Description: Script to create .yaml configuration file to run job_array with slurm for preprocessing GEFSv12 Reforecast Data
#
######################################################################

## import libraries
import pandas as pd
from datetime import timedelta
import numpy as np
import yaml
from itertools import chain

## for each year between 2000 and 2019
date_lst = []
for i, yr in enumerate(range(2000, 2001)):
    # ## get 55 days before November 21
    # center_date = '{0}-11-21'.format(yr)
    # center_date = pd.to_datetime(center_date)
    # start_date = center_date - timedelta(days=55)    
    # ## get 45 days after November 21
    # end_date = center_date + timedelta(days=45)
    # ## make a list of dates between start_date and end_date
    # dates = pd.date_range(start_date, end_date, freq='1D')
    # date_lst.append(dates)

    ## get the rest of the year
    start_date = pd.to_datetime('{0}-01-01'.format(yr))
    end_date = pd.to_datetime('{0}-01-06'.format(yr))
    
    ## make a list of dates between start_date and end_date
    dates = pd.date_range(start_date, end_date, freq='1D')
    
    date_lst.append(dates)

## concatenate all years together into single list    
final_lst = np.concatenate(date_lst)

jobcounter = 0
filecounter = 0
## loop through to create dictionary for each job
d_lst = []
dest_lst = []
njob_lst = []
for i, date in enumerate(final_lst):
    jobcounter += 1
    t = pd.to_datetime(str(date)) 
    yr = t.strftime("%Y")
    dt = t.strftime("%Y%m%d")
    d = {'job_{0}'.format(jobcounter):
         {'year': yr,
          'date': dt}}
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
        call_string = "python preprocess_GEFSv12_reforecast.py config_{0}.yaml 'job_{1}'".format(i+1, j+1)
        call_str_lst.append(call_string)
        
    ## now write those lines to a text file
    with open('calls_{0}.txt'.format(i+1), 'w',encoding='utf-8') as f:
        for line in call_str_lst:
            f.write(line)
            f.write('\n')
        f.close()