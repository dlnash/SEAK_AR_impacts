"""
Filename:    getGFS_batch.py
Author:      Deanna Nash, dnash@ucsd.edu
Description: Download GFS data based on input configuration dictionary.

"""
import sys
import yaml
import subprocess

### Imports config name from argument when submit
yaml_doc = sys.argv[1]
config_name = sys.argv[2]

# import configuration file for dictionary choice
config = yaml.load(open(yaml_doc), Loader=yaml.SafeLoader)
ddict = config[config_name]

init_date = ddict['init_date']
data_name = ddict['data_name']

## run download_GEFS.sh to download data 
bash_script = "/home/dnash/repos/SEAK_AR_impacts/downloads/GFS/download_GFS.sh"
print(subprocess.run([bash_script, init_date, data_name]))