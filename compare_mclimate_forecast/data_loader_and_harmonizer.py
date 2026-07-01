"""
Filename:    data_loader_and_harmonizer.py
Author:      Deanna Nash, dnash@ucsd.edu
Description: Functions for loading forecast data (GEFSv12 Reforecast, GEFS Archive, or GEFS operational) and the associated M-Climate data
Also cleans up and aligns forecast and mclimate so they are directly comparable.
"""

import pandas as pd
import os
import xarray as xr
import numpy as np

from config import DOY_BLOCKS
import globalvars

path_to_data = globalvars.path_to_data

def subset_domain(ds, domain):

    lat = ds.latitude

    # handle ascending vs descending latitude
    if lat[0] > lat[-1]:
        lat_slice = slice(domain["lat_max"], domain["lat_min"])
    else:
        lat_slice = slice(domain["lat_min"], domain["lat_max"])

    return ds.sel(
        longitude=slice(domain["lon_min"], domain["lon_max"]),
        latitude=lat_slice,
    ).sortby('latitude')

def standardize_coords(ds):

    coord_map = {
        "lat": "latitude",
        "lon": "longitude",
        "step": "lead_time",
        "time": "init_date",
    }

    var_map = {
        "tp": "qpf",
    }

    coord_rename = {
        k: v for k, v in coord_map.items()
        if k in ds.coords or k in ds.dims
    }

    var_rename = {
        k: v for k, v in var_map.items()
        if k in ds.data_vars
    }

    ds = ds.rename(coord_rename)
    ds = ds.rename(var_rename)

    return ds

def harmonize_datasets(
    forecast,
    mclimate,
    varname,
    ensemble_mean=True,
    domain=None,
):
    """
    Harmonize forecast and mclimate datasets
    so they are directly comparable.
    """
    print('Harmonizing forecast and mclimate datasets')
    # -------------------------------------------------
    # 1. Rename coordinates
    # -------------------------------------------------

    forecast = standardize_coords(forecast)
    print(forecast)
    mclimate = standardize_coords(mclimate)
    print(mclimate)
    
    # -------------------------------------------------
    # 2. Spatial subset
    # -------------------------------------------------

    forecast = subset_domain(forecast, domain)
    mclimate = subset_domain(mclimate, domain)

    # -------------------------------------------------
    # 3. Ensemble mean
    # -------------------------------------------------

    if ensemble_mean and "number" in forecast.dims:
        forecast = forecast.mean("number")

    # -------------------------------------------------
    # 4. Rename vars
    # -------------------------------------------------
    mclimate = mclimate.rename({f"{varname}_percentiles": varname})


    # -------------------------------------------------
    # 5. Convert lead times to integer hours
    # -------------------------------------------------

    if np.issubdtype(forecast.lead_time.dtype, np.timedelta64):

        lead_hours = (
            forecast.lead_time.values
            / np.timedelta64(1, "h")
        ).astype(int)

        forecast = forecast.assign_coords(
            lead_time=lead_hours
        )

    # -------------------------------------------------
    # 6. Match lead times
    # -------------------------------------------------

    common_leads = np.intersect1d(
        forecast.lead_time,
        mclimate.lead_time,
    )

    forecast = forecast.sel(lead_time=common_leads)
    mclimate = mclimate.sel(lead_time=common_leads)

    # -------------------------------------------------
    # 7. Regrid if needed
    # -------------------------------------------------

    if (
        not forecast.latitude.equals(mclimate.latitude)
        or not forecast.longitude.equals(mclimate.longitude)
    ):

        forecast = forecast.interp(
            latitude=mclimate.latitude,
            longitude=mclimate.longitude,
        )

    # -------------------------------------------------
    # 8. Standard dimension ordering
    # -------------------------------------------------

    dim_order = [
        d for d in [
            "lead_time",
            "latitude",
            "longitude",
        ]
        if d in forecast.dims
    ]

    forecast = forecast.transpose(*dim_order)
    # mclimate = mclimate.transpose(*dim_order)

    return forecast, mclimate

def load_reforecast(init_date, varname):

    init_date = pd.to_datetime(init_date)

    filename = os.path.join(
        path_to_data,
        "preprocessed/GEFSv12_reforecast",
        f"{varname}_final",
        f"GEFSv12_reforecast_{varname}_{init_date:%Y%m%d}.nc",
    )

    print(filename)

    ds = xr.open_dataset(filename, decode_timedelta=True)

    return ds

def load_gefs_archive(init_date, varname):

    init_date = pd.to_datetime(init_date)

    filename = os.path.join(
        path_to_data,
        "preprocessed/GEFS_archive",
        f"{varname}",
        f"{init_date:%Y%m%d}_{varname}.nc",
    )

    print(filename)

    ds = xr.open_dataset(filename, decode_timedelta=True)

    return ds

def load_mclimate(init_date, varname, doy_blocks, base_dir=None):
    """
    Load model climatology dataset based on init_date and DOY blocks.

    Parameters
    ----------
    init_date : str, int, or datetime-like
        Initialization date (e.g., '20000115', 20000115, or datetime)
    varname : str
        Variable name (e.g., 'ivt')
    doy_blocks : dict
        Dictionary of DOY blocks (e.g., DOY_BLOCKS)
    base_dir : str, optional
        Base data directory

    Returns
    -------
    xarray.Dataset
    """

    if base_dir is None:
        base_dir = path_to_data

    # Convert to datetime
    init_date = pd.to_datetime(init_date)
    doy = init_date.dayofyear

    # Handle leap year edge case (optional but recommended)
    if doy == 366:
        doy = 365

    # Find matching DOY block
    block_name = None
    for block in doy_blocks.values():
        if block["doy_min"] <= doy <= block["doy_max"]:
            block_name = block["name"]
            break

    if block_name is None:
        raise ValueError(f"No DOY block found for DOY={doy}")

    # Build filename
    filename = os.path.join(
        base_dir,
        f"preprocessed/mclimate_2.0/{varname}/concat_DOY",
        f"mclimate_{varname}_{block_name}.nc"
    )

    print(f"Loading DOY={doy} → {block_name}")
    print(filename)

    ds = xr.open_dataset(filename)
    ds = ds.sel(doy=doy)

    return ds


def prepare_forecast_and_mclimate(init_date, varname, domain, source="reforecast"):
    if source == "reforecast":
        forecast = load_reforecast(init_date, varname)
    
    elif source == "archive":
        forecast = load_gefs_archive(init_date, varname)
    
    # elif source == "realtime":
    #     forecast = load_gefs(init_date, varname)

    else:
        print('Do not have capability for this source')
        return
    
    mclimate = load_mclimate(
        init_date,
        varname,
        DOY_BLOCKS,
    )
    
    forecast, mclimate = harmonize_datasets(
        forecast=forecast,
        mclimate=mclimate,
        varname=varname,
        domain=domain,
    )

    return forecast, mclimate