######################################################################
# Filename:    compare_mclimate_forecast.py
# Author:      Deanna Nash dnash@ucsd.edu
# Description: Script to take downloaded GEFS_archive or GEFS_reforecast data of a certain initialization date and compare it to mclimate. This will output a Situational Awareness heatmap, a csv file with the heatmap data, and four panel maps for each lead time (every 6 hours from 6 - 168 hours).
#
######################################################################
## import libraries
import os, sys
import yaml
import pandas as pd
import numpy as np

# import personal modules
sys.path.append('/home/dnash/repos/mclimate_tool_cw3e')
from plot_four_panel_fig import output_compare_mclimate_to_reforecast

config_file = str(sys.argv[1]) # this is the config file name
job_info = str(sys.argv[2]) # this is the job name

config = yaml.load(open(config_file), Loader=yaml.SafeLoader) # read the file
ddict = config[job_info] # pull the job info from the dict

## pull information from config file
init_date = ddict['init_date']
model = ddict['model_name']
impact_date = ddict['impact_date']

print('Running comparison for ...')
print('... Impact date: {0}'.format(impact_date))
print('... Initialization date: {0}'.format(init_date))
print('... Model name: {0}'.format(model))
output_compare_mclimate_to_reforecast(init_date, model, impact_date)