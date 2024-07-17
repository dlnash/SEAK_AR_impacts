"""
Filename:    mclimate_funcs.py
Author:      Deanna Nash, dnash@ucsd.edu
Description: Functions for comparing GEFSv12 mClimate to GEFSv12 reforecast
"""

import os, sys
import xarray as xr
import numpy as np
import pandas as pd

def compare_mclimate_to_forecast(fc, mclimate, varname):
    ## compare IVT forecast to mclimate
    b_lst = []
    quant_lst = [0.  , 0.75, 0.9 , 0.91, 0.92, 0.93, 0.94, 0.95, 0.96, 0.97, 0.98, 0.99, 1.  ]
    nquantiles = len(quant_lst)
    for i, quant in enumerate(range(nquantiles)):
        bottom = mclimate[varname].isel(quantile=quant) # minimum threshold
        
        if i == 0:
            # only need to see where variable in the forecast is less than minimum quantile
            b = xr.where(cond=fc[varname] < bottom, x=quant_lst[i], y=np.nan)          
            
        elif (i > 0) & (i < nquantiles-1):
            # where IVT in the forecast is greater than current quartile, but less than next quartile
            top = mclimate[varname].isel(quantile=i+1)
            b = xr.where(cond=(fc[varname] > bottom) & (fc[varname] < top), x=quant_lst[i], y=np.nan)
            b = b.assign_coords({'quantile': (quant_lst[i])})
            
        elif (i == nquantiles-1):
            # where variable is greater than final quartile
            b = xr.where(cond=(fc[varname] > bottom), x=quant_lst[i], y=np.nan)
            b = b.expand_dims(dim="quantile")
    
        b.name = varname
        var_dict = {'mclimate': (['step', 'lat', 'lon'], b.squeeze().values)}
        new_ds = xr.Dataset(var_dict,
                        coords={'lat': (['lat'], b.lat.values),
                                'lon': (['lon'], b.lon.values),
                                'step': (['step'], b.step.values)})     
        b_lst.append(new_ds)
        
    ds = xr.merge(b_lst)

    return ds

def compare_mclimate_to_reforecast(fc, mclimate, varname):
    ## compare IVT reforecast to mclimate
    b_lst = []
    quant_lst = [0.  , 0.75, 0.9 , 0.91, 0.92, 0.93, 0.94, 0.95, 0.96, 0.97, 0.98, 0.99, 1.  ]
    nquantiles = len(quant_lst)
    for i, quant in enumerate(range(nquantiles)):
        bottom = mclimate[varname].isel(quantile=quant) # minimum threshold
        
        if i == 0:
            # only need to see where variable in the forecast is less than minimum quantile
            b = xr.where(cond=fc[varname] < bottom, x=quant_lst[i], y=np.nan)          
            
        elif (i > 0) & (i < nquantiles-1):
            # where IVT in the forecast is greater than current quartile, but less than next quartile
            top = mclimate[varname].isel(quantile=i+1)
            b = xr.where(cond=(fc[varname] > bottom) & (fc[varname] < top), x=quant_lst[i], y=np.nan)
            # b = b.assign_coords({'quantile': (quant_lst[i])})
            
        elif (i == nquantiles-1):
            # where variable is greater than final quartile
            b = xr.where(cond=(fc[varname] > bottom), x=quant_lst[i], y=np.nan)
    
        b.name = varname
        var_dict = {'mclimate': (['lat', 'lon'], b.squeeze().values)}
        new_ds = xr.Dataset(var_dict,
                        coords={'lat': (['lat'], b.lat.values),
                                'lon': (['lon'], b.lon.values)})     
        b_lst.append(new_ds)
        
    ds = xr.merge(b_lst)

    return ds


def load_reforecast(date, varname):
    path_to_data = '/expanse/nfs/cw3e/cwp140/' 
    fname_pattern = path_to_data + 'preprocessed/GEFSv12_reforecast/{0}/{1}_{0}_F*.nc'.format(varname, date)
    forecast = xr.open_mfdataset(fname_pattern, engine='netcdf4', concat_dim="step", combine='nested')
    forecast  = forecast.sortby("step") # sort by step (forecast lead)
    tmp = forecast.step[1::2].values
    forecast = forecast.sel(step=tmp) ## select every 6 hours up to 10 days lead time
    step_vals = forecast.step.values / pd.Timedelta(hours=1)
    forecast = forecast.assign_coords({"step": step_vals.astype(int)})
<<<<<<< HEAD
    if varname == 'ivt':
        forecast = forecast.rename({'longitude': 'lon', 'latitude': 'lat', 'time': 'init_time'}) # need to rename this to match GEFSv12 Reforecast
        forecast = forecast.drop_vars(["ivtu", "ivtv"])
    else:
        forecast = forecast.assign_coords(init_time=(pd.to_datetime(date)))
    forecast = forecast.sel(lon=slice(-179.5, -110.), lat=slice(70., 10.))
=======
    forecast = forecast.rename({'longitude': 'lon', 'latitude': 'lat', 'ivt': 'IVT', 'time': 'init_time'}) # need to rename this to match GEFSv12 Reforecast
    forecast = forecast.sel(lon=slice(-179.5, -110.))
    forecast = forecast.drop_vars(["ivtu", "ivtv"])
>>>>>>> 313ce07730dc805afc4f5d16c3ef9606b85078d3
    forecast = forecast.mean('number') # ensemble mean

    return forecast

<<<<<<< HEAD
def load_mclimate(mon, day, varname):
=======
def load_mclimate(mon, day):
>>>>>>> 313ce07730dc805afc4f5d16c3ef9606b85078d3
    ## special circumstance for leap day
    if (mon == '02') & (day == '29'):
        mon = '02'
        day = '28'
        
    ## load mclimate data
    path_to_data = '/expanse/nfs/cw3e/cwp140/'      # project data -- read only
    fname = path_to_data + 'preprocessed/{2}_mclimate/GEFSv12_reforecast_mclimate_{2}_{0}{1}.nc'.format(mon, day, varname)
    # print(fname_pattern)
<<<<<<< HEAD
    ds = xr.open_dataset(fname)
    # ds = ds.sortby("step") # sort by step (forecast lead)
    if varname == 'ivt':
        ds = ds.rename({'longitude': 'lon', 'latitude': 'lat'}) # need to rename this to match GEFSv12 Reforecast
    else:
        ds = ds
=======
    ds = xr.open_mfdataset(fname_pattern, engine='netcdf4', concat_dim="step", combine='nested')
    ds = ds.sortby("step") # sort by step (forecast lead)
    ds = ds.rename({'longitude': 'lon', 'latitude': 'lat'}) # need to rename this to match GEFSv12 Reforecast
>>>>>>> 313ce07730dc805afc4f5d16c3ef9606b85078d3
    ds = ds.sel(lon=slice(-179.5, -110.), lat=slice(70., 10.))

    return ds
