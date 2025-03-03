## Preprocessing Scripts for SEAK AR Impacts Analysis

After downloading the data (see `../downloads/` for more information), run these preprocessing scripts in this order.

1. **Preprocess GEFSv12_reforecast (2000--2019):** this takes the raw GEFSv12 reforecast data and computes and saves intermediate data for integrated water vapor transport (IVT; kg m-1 s-1), height of the freezing level (m), and 1000 hPa wind (m s-1). The scripts for this can be found in the `GEFSv12_reforecast` directory.

2. **Calculate Model Climate:** this takes the preprocessed GEFSv12 reforecast data and computes the model climate for all three variables for 365 days of the year. For each day of the year (1 Jan to 31 Dec, excluding 29 Feb), forecast lead time (every 6-hr from 6—168 hr), and variable, we computed the the minimum, 75th, 90th, 91st, 92nd, 93rd, 94th, 95th, 96th, 97th, 98th, 99th, and maximum percentile ranks for values within a 45-day period of the day of year. The scripts for this can be found in the `calculate_mclimate` directory.

3. **Preprocess GEFS data (2020--present):** this takes the raw GEFS data and computes and saves intermediate data for integrated water vapor transport (IVT; kg m-1 s-1), height of the freezing level (m), and 1000 hPa wind (m s-1). The scripts for this can be found in the `GEFS` directory.

4. **Compare the forecast/reforecast to the model climate:** for a list of dates with an observed impacts
5. 

