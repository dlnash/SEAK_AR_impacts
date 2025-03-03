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

## load landslide data
fname = path_to_data + 'downloads/Landslide_Data.csv'
df = pd.read_csv(fname)
df = df.set_index(pd.to_datetime(df['Day_min']))
## subset to dates between 2000 and 2024
idx = (df.index >= '2000-01-01') & (df.index <= '2024-12-31')
df = df.loc[idx]

## get unique dates - these are the impact dates
unique_dates = df.index.unique()
unique_dates = unique_dates.sort_values()

## create list of init dates we need 
## we will run mclimate based on these dates and lead times
## for each impact date
## for initialization date 1-7 days before impact date
## F000, F024, F072, ...
date_lst = []
impact_date_lst = []
model_lst = []
for i, date in enumerate(unique_dates):
    ## skip 2 events - 20200227, 20200817
    ## the data from GEFS was too hard to download for these dates
    if (date.strftime("%Y%m%d") == '20200227') | (date.strftime("%Y%m%d") == '20200817'):
        pass
    else:
        for j, init_lead in enumerate(np.arange(1, 8)):
            init_date = date - pd.to_timedelta(init_lead, unit='D')
            date_lst.append(init_date)
            impact_date_lst.append(date)
    
            if init_date.year < 2020:
                model_name = 'GEFSv12_reforecast'
            else:
                model_name = 'GEFS_archive'
    
            model_lst.append(model_name)

d = {'impact_date': impact_date_lst, 'init_date': date_lst, 'model_name': model_lst}
df = pd.DataFrame(d)

jobcounter = 0
filecounter = 0
## loop through to create dictionary for each job
d_lst = []
dest_lst = []
njob_lst = []

for index, row in df.iterrows():
    jobcounter += 1
    
    init_date = row.init_date.strftime('%Y%m%d')
    model = row.model_name
    impact_date = row.impact_date.strftime('%Y%m%d')
    
    d = {"job_{0}".format(jobcounter):
         {"init_date": init_date,
          "model_name": model,
          "impact_date": impact_date
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