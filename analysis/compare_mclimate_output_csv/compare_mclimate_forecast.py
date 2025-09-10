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
import time
import subprocess
start_time = time.time()  # Record the start time

# import personal modules
sys.path.append('/cw3e/mead/projects/cwp140/repos/mclimate_tool_cw3e/')
from plot_four_panel_fig import output_compare_mclimate_to_reforecast

config_file = str(sys.argv[1]) # this is the config file name
job_info = str(sys.argv[2]) # this is the job name

config = yaml.load(open(config_file), Loader=yaml.SafeLoader) # read the file
ddict = config[job_info] # pull the job info from the dict

## pull information from config file
init_date = ddict['init_date']
model = ddict['model_name']

# Example rsync command
source = "/cw3e/mead/projects/cwp140/data/preprocessed/GEFSv12_reforecast/GEFSv12_slope_aspect.nc"
destination = "/dev/shm/GEFSv12_slope_aspect_{0}.nc".format(str(init_date))

# rsync command
command = [
    "rsync",
    "-avh",     # archive, verbose, human-readable
    source,
    destination
]

# Run rsync
subprocess.run(command, check=True)

print('Running comparison for ...')
print('... Initialization date: {0}'.format(init_date))
print('... Model name: {0}'.format(model))
output_compare_mclimate_to_reforecast(init_date, model, plot=False)

end_time = time.time()  # Record the end time
elapsed_time = end_time - start_time  # Calculate duration

print(f"Script took {elapsed_time:.2f} seconds to run.")