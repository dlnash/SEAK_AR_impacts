"""
Filename:    GEFSv12_funcs.py
Author:      Deanna Nash, dnash@ucsd.edu
Description: Functions for preprocessing GEFSv12 reforecast data
"""

import os, sys
import numpy as np
import pandas as pd
import xarray as xr
from datetime import timedelta
from scipy.integrate import trapezoid
import wrf
import glob
import re
# import dask
from functools import partial
# dask.config.set(**{'array.slicing.split_large_chunks': True})

def list_of_processed_trackIDs(varname, server):
    '''
    Returns a list of AR trackIDs that have been processed
    '''
    processed_trackIDs = []
    if server == 'Comet':
        list_of_files = glob.glob('/cw3e/mead/projects/cwp140/scratch/dnash/data/preprocessed/GEFSv12_reforecast/{0}/*_{0}.nc'.format(varname))
    elif server == 'Skyriver':
        list_of_files = glob.glob('/data/projects/Comet/cwp140/preprocessed/GEFSv12_reforecast/{0}/*_{0}.nc'.format(varname))
    else:
        print('Not ready for Expanse')
    
    for fname in list_of_files:

        # pull the initialization date from the filename
        regex = re.compile(r'\d+')
        date_string = regex.findall(fname)
        date_string = date_string[-1]
        date_float = float(date_string)
        processed_trackIDs.append(date_float)

    return processed_trackIDs

def preprocess(ds, start, stop):
    '''keep only selected time step hours'''
    return ds.isel(step=slice(start, stop))


def _preprocess(x, start, stop):
    if x['time'].size > 1:
            x = x.isel(time=0)
    return x.isel(step=slice(start, stop))
    
def fix_GEFSv12_open_mfdataset(fname, start, stop):
    list_of_files = glob.glob(fname)
    ds_lst = []
    for i, fi in enumerate(list_of_files):
        ds = xr.open_dataset(fi)
        if ds['time'].size > 1:
            ds = ds.isel(time=0)
        
        ds_lst.append(ds)

    ## get max step size
    step_size_lst = []
    for i, ds in enumerate(ds_lst):
        step_size_lst.append(ds.step.size)
    max_size = max(step_size_lst)
    max_index = step_size_lst.index(max(step_size_lst))
    max_time = ds_lst[max_index].valid_time.values
    max_ds = ds_lst[max_index]
    ## now loop through and fill ds where smaller than max size
    new_ds_lst = []
    for i, tmp in enumerate(ds_lst):
        if tmp.step.size < max_size:
            new_ds = tmp.reindex_like(max_ds, method='nearest', fill_value=np.nan)
            # new_ds = new_ds.drop_dims("valid_time")
            new_ds = new_ds.assign_coords(valid_time=("step", max_time))
            new_ds = preprocess(new_ds, start, stop)
            # new_ds = ds.expand_dims("valid_time").assign_coords(valid_time=max_time)
            # new_ds = ds.update({"valid_time": max_time})
            # ds1, new_ds = xr.align(ds_above[max_index], ds, join="left")
            new_ds_lst.append(new_ds)
    
        elif tmp.step.size == max_size:
            new_ds = preprocess(tmp, start, stop)
            new_ds_lst.append(new_ds)
        
    ds = xr.concat(new_ds_lst, dim="number")
    
    return ds

def read_and_regrid_prs_var(varname, date, year, start, stop):
    '''
    Using xarray, reads grib data for given variable for above and below 700 mb
    Regrids the data above 700 mb to same horizontal resolution as data below 700 mb
    Merges regridded data and data below 700 mb to single dataset
    Concatenated along ensemble/number axis
    
    returns: ds
        xarray dataset of variable at 0.25 degree horizontal resolution at all given pressure levels
    '''
    
    path_to_data = '/expanse/lustre/scratch/dnash/temp_project/downloaded/GEFSv12_reforecast/{0}/'.format(date) 
    
    # read data below 700 mb - 0.25 degree
    fname = path_to_data+"{0}_pres_{1}00*.grib2".format(varname, date)
    partial_func = partial(_preprocess, start=start, stop=stop)
    
    try:
        ds_below = xr.open_mfdataset(fname, engine='cfgrib', concat_dim="number", combine='nested', preprocess=partial_func)
    except ValueError:
        print('trying alternative method')
        ds_below = fix_GEFSv12_open_mfdataset(fname, start, stop)
    except TypeError:
        print('trying alternative method')
        ds_below = fix_GEFSv12_open_mfdataset(fname, start, stop)
        
    ds_below = ds_below.assign_coords({"longitude": (((ds_below.longitude + 180) % 360) - 180)}) # Convert DataArray longitude coordinates from 0-359 to -180-179
    
    # read data above 700 mb - 0.5 degree
    fname = path_to_data+"{0}_pres_abv700mb_{1}00_*.grib2".format(varname, date)
    try:
        ds_above = xr.open_mfdataset(fname, engine='cfgrib', concat_dim="number", combine='nested', preprocess=partial_func)
    except TypeError:
        print('trying alternative method for above')
        ds_above = fix_GEFSv12_open_mfdataset(fname, start, stop)
    except ValueError:
        print('trying alternative method for above')
        ds_above = fix_GEFSv12_open_mfdataset(fname, start, stop)
    
        
    ds_above = ds_above.assign_coords({"longitude": (((ds_above.longitude + 180) % 360) - 180)}) # Convert DataArray longitude coordinates from 0-359 to -180-179
    
    ## regrid ds_above to same horizontal resolution as ds_below
    regrid_lats = ds_below.latitude.values
    regrid_lons = ds_below.longitude.values
    ds_above = ds_above.interp(longitude=regrid_lons, latitude=regrid_lats)

    ## check for matching sizes
    size_abv = ds_above.step.size
    size_bel = ds_below.step.size
    if size_abv > size_bel:
        ds_below = ds_above.reindex_like(ds_below, method='pad', fill_value=np.nan)
    elif size_abv < size_bel:
        ds_above = ds_below.reindex_like(ds_above, method='pad', fill_value=np.nan)
    
    ## concatenate into single ds
    ds = xr.concat([ds_below, ds_above], dim='isobaricInhPa')

    ## now we can delete ds_below and ds_above since we are done with them
    # del ds_above, ds_below
    
    ## subset to N. America [0, 70, 180, 295]
    ds = ds.sel(latitude=slice(70, 0), longitude=slice(-179.5, -60.))
    
    return ds

def read_sfc_var(varname, date, year, start, stop):
    '''
    Using xarray, reads grib data for given variable for surface level data
    Concatenated along ensemble axis
    
    returns: ds
        xarray dataset of variable at 0.25 degree horizonal resolution for all times
    '''
    
    path_to_data = '/expanse/lustre/scratch/dnash/temp_project/downloaded/GEFSv12_reforecast/{0}/'.format(date)
    
    # read surfaced data
    fname = path_to_data+"{0}_{1}00*.grib2".format(varname, date) 
    partial_func = partial(_preprocess, start=start, stop=stop)
    try:
        ds = xr.open_mfdataset(fname, engine='cfgrib', concat_dim="number", combine='nested', preprocess=partial_func)
    except ValueError:
        print('Trying other option')
        ds = fix_GEFSv12_open_mfdataset(fname, start, stop)

    ## Back to everyone preprocess
    ds = ds.assign_coords({"longitude": (((ds.longitude + 180) % 360) - 180)}) # Convert DataArray longitude coordinates from 0-359 to -180-179
    
    ## subset to N. America [0, 70, 180, 295]
    ds = ds.sel(latitude=slice(70, 0), longitude=slice(-179.5, -60.))
    
    return ds
    
def calc_IVT_manual(ds):
    '''
    Calculate IVT manually (not using scipy.integrate)
    This is in case you need to remove values below the surface
     '''
    if ds.valid_time.size > 8:
        valid_times = ds.valid_time.isel(isobaricInhPa=0).values
    else:
        valid_times = ds.valid_time.values
    pressure = ds.isobaricInhPa.values*100 # convert from hPa to Pa
    dp = np.diff(pressure) # delta pressure
    g = 9.81 # gravity constant
    
    qu_lst = []
    qv_lst = []
    # enumerate through pressure levels so we select the layers
    for i, pres in enumerate(ds.isobaricInhPa.values[:-1]):
        pres2 = ds.isobaricInhPa.values[i+1]
        tmp = ds.sel(isobaricInhPa=[pres, pres2]) # select layer
        tmp = tmp.mean(dim='isobaricInhPa', skipna=True) # average q, u, v in layer
        # calculate ivtu in layer
        qu = ((tmp.q*tmp.u*dp[i])/g)*-1
        qu_lst.append(qu)
        # calculate ivtv in layer
        qv = ((tmp.q*tmp.v*dp[i])/g)*-1
        qv_lst.append(qv)
    
    ## add up u component of ivt from each layer
    qu = xr.concat(qu_lst, pd.Index(pressure[:-1], name="pres"))
    qu = qu.sum('pres')
    qu.name = 'ivtu'
    
    # ## add up v component of ivt from each layer
    qv = xr.concat(qv_lst, pd.Index(pressure[:-1], name="pres"))
    qv = qv.sum('pres')
    qv.name = 'ivtv'
    
    ## calculate IVT magnitude
    ivt = np.sqrt(qu**2 + qv**2)
    ivt.name = 'ivt'

    ds = xr.merge([qu, qv, ivt])
    ds = ds.assign_coords({'valid_time': (['step'], valid_times)})
    
    # # put into a new dataset
    # lat = ds.latitude.values
    # lon = ds.longitude.values
    # step = ds.step.values
    # number = ds.number.values
    # valid_times = ds.valid_time.values
    # initialization_date = ds.time.values
    # ts = pd.to_datetime(str(initialization_date)) 
    # d = ts.strftime("%Y/%m/%d %H:%S")
    
    # var_dict = {'ivtu': (['number', 'step', 'lat', 'lon'], qu),
    #             'ivtv': (['number', 'step', 'lat', 'lon'], qv), 
    #             'ivt': (['number', 'step', 'lat', 'lon'], ivt)}
    # ds = xr.Dataset(var_dict,
    #                 coords={'number': (['number'], number),
    #                         'step': (['step'], step),
    #                         'lat': (['lat'], lat),
    #                         'lon': (['lon'], lon),
    #                         'valid_time': (['step'], valid_times)})
    
    # ds = ds.assign_attrs(init_time=d)
    
    return ds
    
def calc_IVT(ds):
    '''
    Using xarray and preprocessed grib data, calculate IVT
    
    returns: ds
        xarray ds with IVTu, IVTv, and IVT at 0.25 degree
    '''

    # integrate water vapor transport and water vapor
    pressure = ds.isobaricInhPa.values*100 # convert from hPa to Pa
    u = ds.u.values # m s-1
    v = ds.v.values # m s-1
    q = ds.q.values # kg kg-1
    g = 9.81 # gravity constant
    ivtu = (trapezoid(y=u*q, x=pressure, axis=2)/g)*-1
    ivtv = (trapezoid(y=v*q, x=pressure, axis=2)/g)*-1
    ivt = np.sqrt(ivtu**2 + ivtv**2)
    
    # put into a new dataset
    lat = ds.latitude.values
    lon = ds.longitude.values
    initialization_date = ds.time.values
    ts = pd.to_datetime(str(initialization_date)) 
    d = ts.strftime("%Y/%m/%d %H:%S")

    var_dict = {'ivtu': (['number', 'step', 'lat', 'lon'], ivtu),
                'ivtv': (['number', 'step', 'lat', 'lon'], ivtv), 
                'ivt': (['number', 'step', 'lat', 'lon'], ivt)}
    ds = xr.Dataset(var_dict,
                    coords={'number': (['number'], ds.number.values),
                            'step': (['step'], ds.step.values),
                            'lat': (['lat'], lat),
                            'lon': (['lon'], lon),
                            'valid_time': (['step'], ds.valid_time.values)})

    ds = ds.assign_attrs(init_time=d)
    
    return ds

def calc_freezing_level(ds):
    ''' 
    This takes an xarray dataset with geopotential height and temperature at pressure levels
    and reverse interpolates temperature to find the geopotential height of the 0*C isotherm
    
    Returns: ds
        xarray dataset of freezing level (m) at 0.25 degree horizonal resolution
    '''
    
    ## need 2 3D arrays for input
    ## reshape output arrays
    ninit, ntime, nlev, nlat, nlon = ds.gh.shape
    gh = ds.gh.values
    t = ds.t.values-273.15 # convert to *C

    # interpolate gh to temperature = 0
    interp_var = wrf.interplevel(gh, t, [0])

    # put into a dataset
    lat = ds.latitude.values
    lon = ds.longitude.values
    print(interp_var.values.shape)

    var_dict = {'freezing_level': (['number', 'step', 'lat', 'lon'], interp_var.values)}
    ds = xr.Dataset(var_dict,
                    coords={'number': (['number'], ds.number.values),
                            'step': (['step'], ds.step.values),
                            'lat': (['lat'], lat),
                            'lon': (['lon'], lon),
                            'valid_time': (['step'], ds.valid_time.values)})

    return ds