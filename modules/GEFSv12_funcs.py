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

def list_of_processed_trackIDs(varname):
    '''
    Returns a list of AR trackIDs that have been processed
    '''
    processed_trackIDs = []

    list_of_files = glob.glob('/cw3e/mead/projects/cwp140/scratch/dnash/data/preprocessed/GEFSv12_reforecast/{0}/*_{0}.nc'.format(varname))
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

def read_and_regrid_prs_var(varname, ARID, date, year, final_var):
    '''
    Using xarray, reads grib data for given variable for above and below 700 mb
    Regrids the data above 700 mb to same horizontal resolution as data below 700 mb
    Merges regridded data and data below 700 mb to single dataset
    
    returns: ds
        xarray dataset of variable at 0.25 degree horizonal resolution at all given pressure levels
    '''
    
    path_to_data = '/cw3e/mead/projects/cwp140/scratch/dnash/data/downloads/GEFSv12_reforecast/{0}/{1}/'.format(final_var, ARID) 
    
    # read data below 700 mb - 0.25 degree
    fname = path_to_data+"{0}_pres_{1}*_c00.grib2".format(varname, date)
    
    ds_below = xr.open_mfdataset(fname, engine='cfgrib', preprocess=preprocess, concat_dim="initialization", combine='nested')
    ds_below = ds_below.assign_coords({"longitude": (((ds_below.longitude + 180) % 360) - 180)}) # Convert DataArray longitude coordinates from 0-359 to -180-179
    
    # read data above 700 mb - 0.5 degree
    fname = path_to_data+"{0}_pres_abv700mb_*_c00.grib2".format(varname)
    ds_above = xr.open_mfdataset(fname, engine='cfgrib', preprocess=preprocess, concat_dim="initialization", combine='nested')
    ds_above = ds_above.assign_coords({"longitude": (((ds_above.longitude + 180) % 360) - 180)}) # Convert DataArray longitude coordinates from 0-359 to -180-179
    
    ## regrid ds_above to same horizontal resolution as ds_below
    regrid_lats = ds_below.latitude.values
    regrid_lons = ds_below.longitude.values
    ds_above = ds_above.interp(longitude=regrid_lons, latitude=regrid_lats)
    
    ## concatenate into single ds
    ds = xr.concat([ds_below, ds_above], dim='isobaricInhPa')
    
    ## subset to N. Pacific [0, 70, 140, 295]
    ds = ds.sel(latitude=slice(70, 0), longitude=slice(140, -120.))
    
    return ds

def read_sfc_var(varname, varname2, ARID):
    '''
    Using xarray, reads grib data for given variable for surface level data
    For each initialization data, reads only the first 24 hours of data
    
    returns: ds
        xarray dataset of variable at 0.25 degree horizonal resolution for all times
    '''
    
    path_to_data = '/cw3e/mead/projects/cwp140/scratch/dnash/data/downloads/GEFSv12_reforecast/prec/{0}/'.format(ARID) 
    
    # read surfaced data
    fname = path_to_data+"{0}_sfc_*_c00.grib2".format(varname)  
    ds = xr.open_mfdataset(fname, engine='cfgrib', preprocess=preprocess, concat_dim="initialization", combine='nested')
    ds = ds.assign_coords({"longitude": (((ds.longitude + 180) % 360) - 180)}) # Convert DataArray longitude coordinates from 0-359 to -180-179
    
    ## subset to N. Pacific [0, 70, 140, 295]
    ds = ds.sel(latitude=slice(70, 0), longitude=slice(140, -120.))
    
    
    # put into a simple 3D dataset
    time = ds.valid_time.values
    time = time.flatten()
    lat = ds.latitude.values
    lon = ds.longitude.values
    
    # reshape data
    data = ds[varname2].values
    ninit, ntime, nlat, nlon = data.shape
    data = data.reshape(ninit*ntime, nlat, nlon)

    var_dict = {varname2: (['time', 'lat', 'lon'], data)}
    ds = xr.Dataset(var_dict,
                    coords={'time': (['time'], time),
                            'lat': (['lat'], lat),
                            'lon': (['lon'], lon)})
    
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