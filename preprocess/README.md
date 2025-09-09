## Preprocessing Scripts for SEAK AR Impacts Analysis

After downloading the data (see `../downloads/` for more information), run these preprocessing scripts in this order.

1. **Create landslide date lists:** this creates 3 files, one of all reported landslide dates, one of reported landslides dates beyond December 31, 2019 to download GEFS files, and one of non-landslide dates.

2. **Preprocess GEFSv12_reforecast (2000--2019):** this takes the raw GEFSv12 reforecast data and computes and saves intermediate data for integrated water vapor transport (IVT; kg m-1 s-1), height of the freezing level (m), 1000 hPa wind (m s-1), and QPF. The scripts for this can be found in the `GEFSv12_reforecast` directory.

3. **Calculate Model Climate:** this takes the preprocessed GEFSv12 reforecast data and computes the model climate for all four variables for 365 days of the year. For each day of the year (1 Jan to 31 Dec, excluding 29 Feb), forecast lead time (every 6-hr from 6—168 hr), and variable, we computed the the minimum, 75th, 90th, 91st, 92nd, 93rd, 94th, 95th, 96th, 97th, 98th, 99th, and maximum percentile ranks for values within a 45-day period of the day of year. The scripts for this can be found in the `calculate_mclimate` directory. Once model climate is calculated, use the scripts in the `concat_mclimate` directory to concatenate the Model Climate files into 365 files.

4. **Preprocess GEFS data (2020--present):** this takes the raw GEFS data and computes and saves intermediate data for integrated water vapor transport (IVT; kg m-1 s-1), height of the freezing level (m), and 1000 hPa wind (m s-1). The scripts for this can be found in the `GEFS` directory.

5. **Compute Aspect/Slope:** this computes the aspect of the orography based on the GEFS, which is a part of the AR Hazard Index computation.

6. **Compare the forecast/reforecast to the model climate:** for all dates, this creates a csv of the maximum percentile ranks for all of the variables for each lead time

7. **Create maps for designated lead times:** for indicated dates, this creates .png files for lead times every 6 hours out to 168 hours of the AR Hazard Tool

8. **Create time series of IVT data:** this creates a csv file of the IVT values for a given lat/lon based on ERA5

