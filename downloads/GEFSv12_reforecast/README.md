## Download GEFSv12 Reforecast

This directory contains the scripts necessary to download GEFSv12 Reforecast data using job array slurm scripts. There are three variables sets that can be downloaded for the control and 4 ensemble members at all lead times using aws-cli to access the data from [https://registry.opendata.aws/noaa-gefs-reforecast/](https://registry.opendata.aws/noaa-gefs-reforecast/).

1. IVT: This will download u, v, q, on all pressure levels and surface pressure in order to calculate IVT.

2. Freezing Level: This will download geopotential height and temperature on all pressure levels in order to reverse interpolate the height of the zero degree isotherm.

3. UV1000: This will download u and v at pressure levels below 700 mb in order to extrapolate u and v wind at 1000 hPa.