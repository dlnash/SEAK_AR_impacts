######################################################################
# Filename:    concat_mclimate.py
# Author:      Deanna Nash dnash@ucsd.edu
# Description: Script to concatenate mclimate for GEFSv12 Reforecast along lead time blocks.
#
######################################################################
import os
import sys
import xarray as xr
import glob
import gc
import yaml
from datetime import datetime
from config import DOY_BLOCKS

# ---------------------------------------------------------------------
# Main Script
# ---------------------------------------------------------------------
startTime = datetime.now()
varname = 'ivt'
path = f"/cw3e/mead/projects/cwp140/data/preprocessed/mclimate_2.0/{varname}"

# -------------------------------
# Lead time block passed by slurm
# -------------------------------
doy_block_id = int(sys.argv[1])
doy = DOY_BLOCKS[doy_block_id]["name"]

print(f"\nConcatenating {doy}")


files = sorted(glob.glob(
    os.path.join(path, f"mclimate_{varname}_LT_*_{doy}.nc")
))

print(f"  {len(files)} files")

datasets = [xr.open_dataset(f) for f in files]
ds = xr.concat(datasets, dim="lead_time")

ds = ds.chunk({
    "doy": 20,
    "lead_time": 1,
    "quantile": 13,
    "latitude": 141,
    "longitude": 240
})

ds = ds.transpose("doy", "lead_time", "quantile", "latitude", "longitude")
print(ds)

out_name = os.path.join(path, f"concat_DOY/mclimate_{varname}_{doy}.nc" ) 
tmp = out_name + ".tmp"

encoding = {
    f"{varname}_percentiles": {
        "zlib": True,
        "complevel": 4,
        "dtype": "float32"
    }
}

delayed = ds.to_netcdf(
    tmp,
    format="NETCDF4",
    engine="netcdf4",
    encoding=encoding,
    compute=False
)

delayed.compute()

os.replace(tmp, out_name)
ds.close()

print(f"  Saved → {out_name}")

print("\n===============================================")
print(" Workflow Complete")
print(" Total Time:", datetime.now() - startTime)
print("===============================================\n")