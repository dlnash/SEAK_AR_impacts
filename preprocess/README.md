## Preprocessing Scripts for SEAK AR Impacts Analysis

1. preprocess_AR_6-hourly.py

This script generates a .csv 6-hourly and daily time series of days an AR makes landfall in southeast Alaska 

2. create_job_configs.py

This script creates a .yaml and .txt file for each of the variables (e.g., freezing level, precipitation, and IVT). The .yaml file is a dictionary of the parameters needed to run download_and_preprocess_GEFSv12_var.py and the .txt file is the call to run via job array in SLURM. 
    
3. run_prep_var.slurm

This script uses SLURM and job array to download and preprocess IVT, freezing level, and precipitation for GEFSv12. This script relies on the .yaml and .txt files generated from create_job_configs.py

3. preprocess_database.py

TODO: This script connects tARget v3 (AR duration data), GEFSv12 (IVT, precipitation, snow level), impact data (NWS), and ASOS/COOP (precipitation) data into a single dataframe and saves as a .csv.

