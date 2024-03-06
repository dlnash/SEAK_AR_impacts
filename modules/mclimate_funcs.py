"""
Filename:    mclimate_funcs.py
Author:      Deanna Nash, dnash@ucsd.edu
Description: Functions for comparing GEFSv12 mClimate to GEFSv12 reforecast
"""

import os, sys
import xarray as xr
import numpy as np

def compare_mclimate_to_forecast(fc, mclimate):
    ## compare IVT forecast to mclimate
    b_lst = []
    quant_lst = [0.  , 0.75, 0.9 , 0.91, 0.92, 0.93, 0.94, 0.95, 0.96, 0.97, 0.98, 0.99, 1.  ]
    nquantiles = len(quant_lst)
    for i, quant in enumerate(range(nquantiles)):
        bottom = mclimate.ivt.isel(quantile=quant).squeeze() # minimum threshold
        
        if i == 0:
            # only need to see where IVT in the forecast is less than minimum quantile
            b = xr.where(cond=fc.IVT < bottom, x=quant_lst[i], y=np.nan)
            
        elif (i > 0) & (i < nquantiles-1):
            # where IVT in the forecast is greater than current quartile, but less than next quartile
            top = mclimate.ivt.isel(quantile=i+1)
            b = xr.where(cond=(fc.IVT > bottom) & (fc.IVT < top), x=quant_lst[i], y=np.nan)
            
        elif (i == nquantiles-1):
            # where IVT is greater than final quartile
            b = xr.where(cond=(fc.IVT > bottom), x=quant_lst[i], y=np.nan)
    
        b.name = 'ivt'
        
        var_dict = {'ivt_mclimate': (['lat', 'lon'], b.squeeze().values)}
        new_ds = xr.Dataset(var_dict,
                        coords={'lat': (['lat'], b.lat.values),
                                'lon': (['lon'], b.lon.values)})
        
        b_lst.append(new_ds)
            
    ds = xr.merge(b_lst)

    return ds

def load_reforecast(date, varname):
    path_to_data = '/expanse/nfs/cw3e/cwp140/'      # project data -- read only
    fname = path_to_data + 'preprocessed/GEFSv12_reforecast/{0}/{1}_{0}_F51_F72.nc'.format(varname, date)
    forecast = xr.open_dataset(fname)
    forecast = forecast.rename({'longitude': 'lon', 'latitude': 'lat', 'ivt': 'IVT'}) # need to rename this to match GEFSv12 Reforecast
    forecast = forecast.sel(lon=slice(-179.5, -110.))
    forecast = forecast.drop_vars(["ivtu", "ivtv"])
    forecast = forecast.isel(step=-1) ### need to fix this so it selects the right time step based on input
    forecast = forecast.mean('number') # ensemble mean

    return forecast

def load_mclimate(mon, day, lead=72):
    ## special circumstance for leap day
    if (mon == 2) & (day == 29):
        mon = 2
        day = 28
        
    ## load mclimate data
    path_to_data = '/expanse/nfs/cw3e/cwp140/'      # project data -- read only
    fname_pattern = path_to_data + 'preprocessed/mclimate/GEFSv12_reforecast_mclimate_ivt_{0}{1}_*hr-lead.nc'.format(mon, day)
    # print(fname_pattern)
    ds = xr.open_mfdataset(fname_pattern, engine='netcdf4', concat_dim="step", combine='nested')
    ds = ds.sortby("step") # sort by step (forecast lead)
    ds = ds.rename({'longitude': 'lon', 'latitude': 'lat'}) # need to rename this to match GEFSv12 Reforecast
    ds = ds.sel(step=lead, lon=slice(-179.5, -110.), lat=slice(70., 10.))

    return ds
