"""
Filename:    download_ERA5_IVT.py
Author:      Deanna Nash, dnash@ucsd.edu
Description: Download a subset of ERA5 data for given dates
"""

import cdsapi
import pandas as pd
sys.path.append('../modules')
import globalvars

path_to_data = globalvars.path_to_data
# Initialize CDS API client
c = cdsapi.Client()

# Define download parameters
dataset = 'reanalysis-era5-single-levels'
product_type = 'reanalysis'
variables = ['vertical_integral_of_northward_water_vapour_flux', 'vertical_integral_of_eastward_water_vapour_flux'] # Add desired variables
data_format = 'netcdf' # or 'grib'

# Define start and end dates for the download
start_date = '2020-11-27'
end_date = '2020-12-05' 

# Generate a list of dates for the request
dates = pd.date_range(start=start_date, end=end_date, freq='D').strftime('%Y-%m-%d').tolist()

# Generate a list of all hours in a day
times = [f'{hour:02d}:00' for hour in range(24)]

# Loop through each day and retrieve data
for day in dates:
    request = {
        'product_type': product_type,
        'variable': variables,
        'year': day.split('-')[0],
        'month': day.split('-')[1],
        'day': day.split('-')[2],
        'time': times,
        'area': [54, -141, 60, -130],# [S,W,N,E] Default: global
        'format': data_format,
    }
    target_file = path_to_data+f'downloads/ERA5/era5_data_{day}.nc' # Output file name for each day

    print(f"Downloading data for {day}...")
    c.retrieve(
        dataset,
        request,
        target_file
    )
    print(f"Download complete for {day}: {target_file}")