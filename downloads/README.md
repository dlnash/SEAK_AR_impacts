## Download data for SEAK AR Impacts Analysis

1. Download the AR detection result

Navigate to [https://dataverse.ucla.edu/dataverse/ar](https://dataverse.ucla.edu/dataverse/ar) and select 'globalARcatalog_NCEP-NCAR_1948-2021_v3.0.nc' to download. You will need to provide information regarding the use of this dataset.

2. Download ASOS/COOP precipitation gauge data from Mesowest.

ASOS/COOP precipitation gauge data from 2002 is available at [https://mesowest.utah.edu/](https://mesowest.utah.edu/). 

3. Download the Global Ensemble Forecast System Version 12: Reforecast Data (2000-2019)

Variables included in the download are U (ugrd_pres, ugrd_pres_abv700mb), V (vgrd_pres, vgrd_pres_abv700mb), and Q (spfh_pres, spfh_pres_abv700mb) for IVT. For freezing level, variables included in the download are T (tmp_pres, tmp_pres_abv700mb) and Z (hgt_pres, hgt_pres_abv700mb). Script will access Day 1-10 reforecast data via AWS for every day of the year for the control and 4 ensemble members. 

You will need awscli installed on your machine. To learn more, visit [https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-welcome.html](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-welcome.html). 

This workflow utilizes job array via slurm. In `downloads/GEFSv12_reforecast/`, run:

```
sbatch run_download_GEFSv12_reforecast.slurm

## Note: you will need to edit Line 20 to reflect which list of calls you are currently processes. (e.g., to process calls_1.txt, modify the end of Line 20 to read "calls_1.txt"

```

4. Download southeast Alaska WRF data from Lader et al., 2020

You will need awscli installed on your machine.
[https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-welcome.html](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-welcome.html). 

This workflow utilizes job array via slurm. In `downloads/WRF/`, run:

```
sbatch run_download_WRF.slurm

## Note: you will need to edit Line 20 to reflect which list of calls you are currently processes. (e.g., to process calls_1.txt, modify the end of Line 20 to read "calls_1.txt"

```

5. Download the Global Ensemble Forecast System data (2017 to present)

Scripts in the`downloads/GEFS/` directory will download the raw .grb forecast files for the chosen date from 2017 to present day. This data can be used to compare the model climate to a forecast date after 2019, which is as far as the reforecast extends.