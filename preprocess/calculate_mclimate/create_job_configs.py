######################################################################
# Filename:    create_job_configs.py
# Author:      Deanna Nash dnash@ucsd.edu
# Description: Script to create .yaml configuration file to run job_array with slurm for calculating M-Climate for GEFSv12 Reforecast Data
#
######################################################################

## import libraries
import pandas as pd
from datetime import timedelta
import numpy as np
import yaml
from itertools import chain

dates = pd.date_range('2023-01-06', '2023-01-12', freq='1D') ## final dates for MClimate

month_lst = dates.strftime("%m") # month array
day_lst = dates.strftime("%d") # day array
F_lst = np.arange(6, 243, 6) # forecast lead list

jobcounter = 0
filecounter = 0
## loop through to create dictionary for each job
d_lst = []
dest_lst = []
njob_lst = []
for i, (mon, day) in enumerate(zip(month_lst, day_lst)):
    for j, F in enumerate(F_lst):
        jobcounter += 1

        d = {'job_{0}'.format(jobcounter):
             {'month': mon,
              'day': day,
              'F': str(F)
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
        call_string = "python calc_mclimate.py config_{0}.yaml 'job_{1}'".format(i+1, j+1)
        call_str_lst.append(call_string)
        
    ## now write those lines to a text file
    with open('calls_{0}.txt'.format(i+1), 'w',encoding='utf-8') as f:
        for line in call_str_lst:
            f.write(line)
            f.write('\n')
        f.close()
