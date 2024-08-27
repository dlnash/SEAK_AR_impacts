## Download GEFSv12 Reforecast

This directory contains the scripts necessary to download GEFSv12 Reforecast data using job array slurm scripts. There are three variables sets that can be downloaded for the control and 4 ensemble members at all lead times using aws-cli to access the data from [https://registry.opendata.aws/noaa-gefs-reforecast/](https://registry.opendata.aws/noaa-gefs-reforecast/).

1. IVT: This will download u, v, q, on all pressure levels and surface pressure in order to calculate IVT.

2. Freezing Level: This will download geopotential height and temperature on all pressure levels in order to reverse interpolate the height of the zero degree isotherm.

3. UV1000: This will download u and v at pressure levels below 700 mb in order to extrapolate u and v wind at 1000 hPa.


To run, first you will need to create the calls_x.txt and config_x.yaml files for the slurm job array. in `create_job_configs.py` edit the `start_date` and `end_date` to select the date range you would like to download. Then, in the terminal, run `conda activate SEAK-impacts` and then `python create_job_configs.py`. This should create a number of files that will be used in the slurm script. 

Next, confirm that the variable you would like to download is chosen by editing the `varname` in `getGEFSv12_batch.py` script. The options are `ivt`, `freezing_level`, or `uv1000` as described above.

Last, you will need to use slurm to run through your various `calls_x.txt` scripts. Ensure the options in `run_download_GEFSv12_reforecast.slurm` script are correct for the current `calls_x.txt` script you are running, then submit the job array by running `sbatch run_download_GEFSv12_reforecast.slurm` in the Expanse command line.