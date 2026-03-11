import os, sys
import xarray as xr
import pandas as pd
import numpy as np
from datetime import datetime
import gc
import yaml
from config import DOY_BLOCKS, LEAD_TIME_BLOCKS

path_to_data = '/cw3e/mead/projects/cwp140/data/'     # project data -- read only

# ---------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------
def init_to_file(t):
    return (
        f"{path_to_data}preprocessed/GEFSv12_reforecast/"
        f"{varname}_final/"
        f"GEFSv12_reforecast_{varname}_{t:%Y%m%d}.nc"
    )
    
def doy_range_with_padding(doy_min, doy_max, window, year_length=365):
    """
    Returns a sorted list of DOYs (1–365) needed to cover
    [doy_min, doy_max] with ±window padding, accounting for wrap.
    """
    start = doy_min - window
    end   = doy_max + window

    doys = []
    for d in range(start, end + 1):
        if d < 1:
            doys.append(d + year_length)
        elif d > year_length:
            doys.append(d - year_length)
        else:
            doys.append(d)

    return sorted(set(doys))

    
def circular_doy_distance(doy, target_doy, year_length=365):
    """
    doy: xarray.DataArray of day-of-year values
    target_doy: int (1–365)
    """
    diff = abs(doy - target_doy)
    return xr.where(diff <= year_length / 2, diff, year_length - diff)

def preprocess(ds):
    if varname == 'ivt':
        ds = ds.drop_vars(["ivtu", "ivtv"], errors="ignore")
    
    # Convert step to timedelta64[ns] safely
    ds["step"] = ds["step"].astype("timedelta64[ns]")
    
    # Select the nearest lead time
    F_lst = np.array(lt_cfg["lead_times"], dtype="timedelta64[h]")
    ds = ds.sel(step=F_lst, method="nearest")
   
    return ds


# ---------------------------------------------------------------------
# Main Script
# ---------------------------------------------------------------------
startTime = datetime.now()

# -------------------------------
# Inputs passed to this script
# -------------------------------
config_file, job_info = sys.argv[1], sys.argv[2]

# --- Load configuration ---
with open(config_file, "r") as f:
    config = yaml.safe_load(f)

ddict = config[job_info]
varname = ddict["varname"]
lt_block_id = ddict["lt_block_id"]
doy_block_id = ddict["doy_block_id"]

window = 10
years = range(2000, 2020)

# Build DOYs to load 
doy_cfg = DOY_BLOCKS[doy_block_id]
lt_cfg  = LEAD_TIME_BLOCKS[lt_block_id]

## Returns a sorted list of DOYs (1–365) needed to cover
## [doy_min, doy_max] with ±window padding, accounting for wrap.
data_doys = doy_range_with_padding(
    doy_cfg["doy_min"],
    doy_cfg["doy_max"],
    window,
)

## Convert that list into a list of init_dates
## This helps us  create a list of init_dates so we know which files to open
valid_dates = []

for y in years:
    jan1 = pd.Timestamp(f"{y}-01-01")
    for doy in data_doys:
        valid_dates.append(jan1 + pd.Timedelta(days=doy - 1))

valid_dates = pd.to_datetime(valid_dates)

# Convert valid → init
init_dates = []
for lt in lt_cfg["lead_times"]:
    init_dates.extend(valid_dates - pd.Timedelta(hours=lt))

files = sorted({
    init_to_file(t)
    for t in init_dates
    if os.path.exists(init_to_file(t))
})

print(len(files))

print(f"DOY Block {doy_block_id} ({doy_cfg["name"]}) | Lead Time Block {lt_block_id} ({lt_cfg["name"]}): {len(files)} files")
print("Elapsed:", datetime.now() - startTime)
# One SLURM job per lead time (or 6–12 lead times per job)
# Inside each job, use xarray + dask to compute model climates for all days.
print("Reading data...")

# open_mfdataset(...) for all years
ds = xr.open_mfdataset(
    files,
    combine="nested",
    concat_dim="time",
    preprocess=preprocess,
    chunks={"time":50,"number":-1},
    data_vars="minimal",
    coords="minimal",
    compat="override",
    parallel=False,
    decode_cf=True,   # Let xarray handle 'time' and 'step'
)

# print(ds.time.values)
# print(ds.step.values)

# Create valid_time as a 2D coordinate: dims=("time", "step")
ds = ds.assign_coords(
    valid_time=(("time", "step"), ds["time"].values[:, None] + ds["step"].values[None, :])
)

print(ds)
print(ds.valid_time.values)
ds = ds[[varname]].load()


a = np.array([0.0, 0.75, 0.9])
b = np.arange(0.91, 1.001, 0.01)
quantile_arr = np.concatenate((a, b))
    
# -----------------------------
# Compute Percentiles
# -----------------------------
print("Elapsed:", datetime.now() - startTime)
print("Computing percentiles...")

# Store results per lead time and DOY
pct_lt_list = []  # one entry per lead time

for lt in lt_cfg["lead_times"]:
    print(f"Processing lead time {lt} h...")
    print("Elapsed:", datetime.now() - startTime)

    # Select single lead time
    ds_lt = ds.sel(step=np.timedelta64(lt, "h"))
    
    # 1D day-of-year for this lead time
    doy_1d = ds_lt.valid_time.dt.dayofyear
    
    pct_doy_list = []  # one entry per DOY

    for target_doy in range(doy_cfg["doy_min"], doy_cfg["doy_max"] + 1):

        mask = circular_doy_distance(doy_1d, target_doy) <= window
        samples = ds_lt[varname].where(mask, drop=True)

        if samples.sizes.get("time", 0) == 0:
            continue

        # Compute quantiles
        pct = samples.quantile(
            q=quantile_arr,
            dim=("time", "number"),
        ).astype("float32")
        
        pct = (
            pct
            .assign_coords(doy=target_doy)
            .expand_dims("doy")
        )

        pct_doy_list.append(pct)
    
    del samples
    # ---- CONCAT DOY FIRST ----
    pct_lt = xr.concat(
        pct_doy_list,
        dim="doy",
        join="exact"
    )

    # attach single lead_time coordinate
    pct_lt = (
        pct_lt
        .assign_coords(lead_time=lt)
        .expand_dims("lead_time")
    )

    pct_lt_list.append(pct_lt)
del ds, ds_lt

print('PRINTING HERE FOR DEBUG')
print(pct_lt_list[0])
pct_all = xr.concat(
    pct_lt_list,
    dim="lead_time",
    join="exact"
)

pct_all = pct_all.rename(f"{varname}_percentiles")

# Update metadata
pct_all.attrs.update({
    "description": f"GEFSv12 model climate percentiles for {varname}",
    "lead_time_hours": lt_cfg["lead_times"],
    "doy_window": window,
    "doy_block": f"{doy_cfg['doy_min']}-{doy_cfg['doy_max']}",
    "years": "2000–2019",
    "created_by": os.environ.get("USER", "unknown"),
})

# Done, pct_all ready to save
print(pct_all)

# -----------------------------
# Save to NetCDF
# -----------------------------
print("Elapsed:", datetime.now() - startTime)
print("Write to netCDF...")
out_dir = os.path.join(
    path_to_data,
    f"preprocessed/mclimate_2.0/{varname}"
)
os.makedirs(out_dir, exist_ok=True)

out_name = os.path.join(
    out_dir,
    f"mclimate_{varname}_{lt_cfg['name']}_{doy_cfg['name']}.nc"
)


def encoding_da(da, zlib=True, complevel=5):
    return {
        da.name: {
            "zlib": zlib,
            "complevel": complevel,
            "dtype": "float32",
        }
    }

tmp_name = out_name + ".tmp"

pct_all.to_netcdf(
    tmp_name,
    mode="w",
    format="NETCDF4",
    encoding=encoding_da(pct_all),
)

os.replace(tmp_name, out_name)
print(f"Saved: {out_name}")

print("\n===============================================")
print(" Workflow Complete")
print(" Total Time:", datetime.now() - startTime)
print("===============================================\n")