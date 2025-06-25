"""
Filename:    getGEFSv12_batch.py
Author:      Deanna Nash, dnash@ucsd.edu
Description: Download GEFSv12 Reforecast data based on input configuration dictionary.

"""
import sys
import yaml
import subprocess

### Imports config name from argument when submit
yaml_doc = sys.argv[1]
config_name = sys.argv[2]

# import configuration file for season dictionary choice
config = yaml.load(open(yaml_doc), Loader=yaml.SafeLoader)
ddict = config[config_name]

year = ddict['year']
date = ddict['date']
varname = 'prec' ## can be 'ivt', 'freezing_level', 'prec', 'uv1000'

## run download_GEFSv12_reforecast.sh to download data 
bash_script = "/home/dnash/repos/SEAK_AR_impacts/downloads/GEFSv12_reforecast/download_GEFSv12_reforecast.sh"
print(subprocess.run([bash_script, year, date, varname]))