"""
Filename:    getGEFS_batch.py
Author:      Deanna Nash, dnash@ucsd.edu
Description: Download GEFS data based on input configuration dictionary.

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
ens = ddict['ens']

## run download_GEFS.sh to download data 
bash_script = "/cw3e/mead/projects/cwp140/repos/SEAK_AR_impacts/downloads/GEFS/download_GEFS.sh"
print(subprocess.run([bash_script, init_date, data_name, ens]))