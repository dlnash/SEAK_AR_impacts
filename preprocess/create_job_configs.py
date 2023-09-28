######################################################################
# Filename:    create_job_configs.py
# Author:      Deanna Nash dnash@ucsd.edu
# Description: Script to create .yaml configuration file to run job_array with slurm
#
######################################################################

## import libraries
import os, sys
import yaml
import pandas as pd

sys.path.append('../modules')
import GEFSv12_funcs as gefs

def create_job_config_file(varname):
    ## pull filenames from preprocessed directory into a list of trackIDs
    complete_trackID = gefs.list_of_processed_trackIDs(varname)
    
    ## read AR duration file
    duration_df = pd.read_csv('../out/AR_track_duration_SEAK.csv')
    
    ## keep only rows where we haven't preprocessed the dates yet
    idx = ~duration_df['trackID'].isin(complete_trackID)
    duration_df = duration_df[idx]
    
    ## create df with just ARID, start, stop
    df = duration_df.drop(['Unnamed: 0', 'duration'], axis=1)

    ## modify trackID to be a string
    df['trackID'] = df['trackID'].astype(int)
    df['trackID'] = df['trackID'].astype(str)
    
    # create job_id column
    job_lst = []
    njobs = len(df)
    for x in range(1, njobs+1):
        job_lst.append('job_{0}'.format(str(x)))
    df.insert(0, 'job_id', job_lst)
    
    ## set job_id to index
    df.index = df['job_id']
    df = df.drop(['job_id'], axis=1)
    
    ## export to .yaml
    job_dict = df.to_dict('index')
    
    file=open("config_{0}.yaml".format(varname),"w")
    yaml.dump(job_dict,file)
    file.close()

    return njobs

## loop through variables to create config file for each variable
var_lst = ['ivt', 'prec', 'freezing_level']
njobs_lst = []
for i, varname in enumerate(var_lst):
    njobs = create_job_config_file(varname)
    njobs_lst.append(njobs)

## now loop through variables and number of jobs to create calls.txt for each variable
for i, varname in enumerate(var_lst):
    njobs = njobs_lst[i]
    call_str_lst = []
    for j, job in enumerate(range(1, njobs+1, 1)):
        call_string = "python download_and_preprocess_GEFSv12_{0}.py config_{0}.yaml 'job_{1}'".format(varname, j+1)
        call_str_lst.append(call_string)
        
    ## now write those lines to a text file
    with open('calls_{0}.txt'.format(varname), 'w',encoding='utf-8') as f:
        for line in call_str_lst:
            f.write(line)
            f.write('\n')
        f.close()