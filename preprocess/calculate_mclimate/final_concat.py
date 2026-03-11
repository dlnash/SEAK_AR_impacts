######################################################################
# Filename:    final_concat.py
# Author:      Deanna Nash dnash@ucsd.edu
# Description: Script to concatenate mclimate for GEFSv12 Reforecast from 10 lead time block files to a single file.
#
######################################################################
import xarray as xr
import glob
import os
from datetime import datetime

startTime = datetime.now()

path = "/cw3e/mead/projects/cwp140/data/preprocessed/mclimate_2.0/ivt/concat_LT/"
files = sorted(glob.glob(os.path.join(path, "mclimate_ivt_LT_*.nc")))

print(f"Found {len(files)} lead time files")

ds = xr.open_mfdataset(
    files,
    combine="by_coords",
    parallel=True
)

ds = ds.transpose("doy", "lead_time", "quantile", "latitude", "longitude")

# chunk so that when we access a single DOY and all lead times, it is the right size.
ds = ds.chunk({
    "doy": 1,
    "lead_time": -1,
    "quantile": -1,
    "latitude": 141,
    "longitude": 240
})

print(ds)
print(ds.ivt_percentiles.data)

out_file = os.path.join(path, "mclimate_ivt_all_leadtimes.nc")

encoding = {
    "ivt_percentiles": {
        "zlib": True,
        "complevel": 4,
        "dtype": "float32"
    }
}

delayed = ds.to_netcdf(
    out_file,
    format="NETCDF4",
    engine="netcdf4",
    encoding=encoding,
    compute=False
)

delayed.compute()

print(f"Saved → {out_file}")
print("\n===============================================")
print(" Workflow Complete")
print(" Total Time:", datetime.now() - startTime)
print("===============================================\n")