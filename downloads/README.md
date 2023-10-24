## Download data for SEAK AR Impacts Analysis

1. Download the AR detection result

Navigate to [https://dataverse.ucla.edu/dataverse/ar](https://dataverse.ucla.edu/dataverse/ar) and select 'globalARcatalog_NCEP-NCAR_1948-2021_v3.0.nc' to download. You will need to provide information regarding the use of this dataset.

2. Download ASOS/COOP precipitation gauge data from Mesowest.

ASOS/COOP precipitation gauge data from 2002 is available at [https://mesowest.utah.edu/](https://mesowest.utah.edu/). 

3. Download the Global Ensemble Forecast System Version 12: Reforecast Data

TODO: Add framework for downloading/preprocessing GEFSv12 Reforecast. Variables include Total Precipitation (apcp_sfc), Precipitable Water (pwat_eatm), U (ugrd_pres, ugrd_pres_abv700mb), V (vgrd_pres, vgrd_pres_abv700mb), T (tmp_pres, tmp_pres_abv700mb), and Q (spfh_pres, spfh_pres_abv700mb). Script will access data via AWS for the duration of each AR event.

You will need awscli installed on your machine. To learn more, visit [https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-welcome.html](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-welcome.html). 

```
# in download directory
bash download_GEFSv12_reforecast.sh
```

