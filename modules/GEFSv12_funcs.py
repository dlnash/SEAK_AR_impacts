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
from scipy.integrate import trapz
import wrf
import glob
import re

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

def preprocess(ds):
    '''keep only the first 24 hours'''
    return ds.isel(step=slice(0, 8))

def fix_GEFSv12_open_mfdataset(fname):
    list_of_files = glob.glob(fname)
    ds_lst = []
    for i, fi in enumerate(list_of_files):
        ds = xr.open_dataset(fi)
        if ds['time'].size > 1:
            ds = ds.isel(time=0)
        ds = preprocess(ds)
        ds_lst.append(ds)
    ds = xr.concat(ds_lst, dim='number')

    return ds

def read_and_regrid_prs_var(varname, date, year):
    '''
    Using xarray, reads grib data for given variable for above and below 700 mb
    Regrids the data above 700 mb to same horizontal resolution as data below 700 mb
    Merges regridded data and data below 700 mb to single dataset
    Concatenated along ensemble/number axis
    
    returns: ds
        xarray dataset of variable at 0.25 degree horizontal resolution at all given pressure levels
    '''
    
    path_to_data = '/cw3e/mead/projects/cwp140/scratch/dnash/data/downloads/GEFSv12_reforecast/{0}/'.format(date) 
    
    # read data below 700 mb - 0.25 degree
    fname = path_to_data+"{0}_pres_{1}00*.grib2".format(varname, date)
    
    try:
        ds_below = xr.open_mfdataset(fname, engine='cfgrib', concat_dim="number", combine='by_coords')
    except ValueError:
        ds_below = fix_GEFSv12_open_mfdataset(fname)
        
    ds_below = ds_below.assign_coords({"longitude": (((ds_below.longitude + 180) % 360) - 180)}) # Convert DataArray longitude coordinates from 0-359 to -180-179
    
    # read data above 700 mb - 0.5 degree
    fname = path_to_data+"{0}_pres_abv700mb_{1}00_*.grib2".format(varname, date)
    try:
        ds_above = xr.open_mfdataset(fname, engine='cfgrib', concat_dim="number", combine='by_coords')
    except ValueError:
        ds_above = fix_GEFSv12_open_mfdataset(fname)
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
    
    ## subset to N. America [0, 70, 180, 295]
    ds = ds.sel(latitude=slice(70, 0), longitude=slice(-179.5, -60.))
    
    return ds

def read_sfc_var(varname, date, year):
    '''
    Using xarray, reads grib data for given variable for surface level data
    Concatenated along ensemble axis
    
    returns: ds
        xarray dataset of variable at 0.25 degree horizonal resolution for all times
    '''
    
    path_to_data = '/cw3e/mead/projects/cwp140/scratch/dnash/data/downloads/GEFSv12_reforecast/{0}/'.format(date)
    
    # read surfaced data
    fname = path_to_data+"{0}_sfc_*.grib2".format(varname) 

    try:
        ds = xr.open_mfdataset(fname, engine='cfgrib', concat_dim="number", combine='by_coords')
    except ValueError:
        ds = fix_GEFSv12_open_mfdataset(fname)

    ## Back to everyone preprocess
    ds = ds.assign_coords({"longitude": (((ds.longitude + 180) % 360) - 180)}) # Convert DataArray longitude coordinates from 0-359 to -180-179
    
    ## subset to N. America [0, 70, 180, 295]
    ds = ds.sel(latitude=slice(70, 0), longitude=slice(-179.5, -60.))
    
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
    ivtu = (trapz(y=u*q, x=pressure, axis=2)/g)*-1
    ivtv = (trapz(y=v*q, x=pressure, axis=2)/g)*-1
    ivt = np.sqrt(ivtu**2 + ivtv**2)
    
    ## reshape output arrays
    ninit, ntime, nlat, nlon = ivt.shape
    ivt = ivt.reshape(ninit*ntime, nlat, nlon)
    ivtu = ivtu.reshape(ninit*ntime, nlat, nlon)
    ivtv = ivtv.reshape(ninit*ntime, nlat, nlon)
    
    # put into a simple 3D dataset
    time = ds.valid_time.values
    time = time.flatten()
    lat = ds.latitude.values
    lon = ds.longitude.values

    var_dict = {'ivtu': (['time', 'lat', 'lon'], ivtu),
                'ivtv': (['time', 'lat', 'lon'], ivtv), 
                'ivt': (['time', 'lat', 'lon'], ivt)}
    ds = xr.Dataset(var_dict,
                    coords={'time': (['time'], time),
                            'lat': (['lat'], lat),
                            'lon': (['lon'], lon)})
    
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
    gh = ds.gh.values.reshape(ninit*ntime, nlev, nlat, nlon)
    t = ds.t.values.reshape(ninit*ntime, nlev, nlat, nlon)-273.15 # convert to *C

    # interpolate gh to temperature = 0
    interp_var = wrf.interplevel(gh, t, [0])

    # put into a simple 3D dataset
    time = ds.valid_time.values
    time = time.flatten()
    lat = ds.latitude.values
    lon = ds.longitude.values

    var_dict = {'freezing_level': (['time', 'lat', 'lon'], interp_var.values)}
    ds = xr.Dataset(var_dict,
                    coords={'time': (['time'], time),
                            'lat': (['lat'], lat),
                            'lon': (['lon'], lon)})

    return ds