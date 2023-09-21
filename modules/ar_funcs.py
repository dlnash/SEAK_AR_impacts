"""
Filename:    ar_funcs.py
Author:      Deanna Nash, dnash@ucsd.edu
Description: Functions for getting AR metrics
"""

# Import Python modules
import os, sys
import yaml
import numpy as np
import xarray as xr
import pandas as pd
from itertools import groupby
import metpy.calc as mpcalc
from metpy.units import units


## FUNCTIONS


def build_empty_df(stationID):
    ## read AR duration file
    duration_df = pd.read_csv('../out/AR_track_duration_SEAK.csv')
    duration_df['start_date'] = pd.to_datetime(duration_df['start_date'])
    duration_df['end_date'] = pd.to_datetime(duration_df['end_date'])
    duration_df.index = duration_df['trackID']
    
    ## build out the dataframe with the information we want to add
    # add empty columns
    duration_df['IVT_max'] = np.nan # maximum IVT during the AR event
    duration_df['IVT_max_time'] = np.nan # timestamp of maximum IVT during the AR event
    duration_df['IVT_dir'] = np.nan # IVT direction at the time of peak IVT
    duration_df['freezing_level'] = np.nan # freezing level at the time of peak IVT
    duration_df['ar_scale'] = np.nan # calculated AR scale based on GEFS 
    duration_df['GFS_prec_accum'] = np.nan # total accumulated precipitation (GEFS)
    duration_df['GFS_prec_max_rate'] = np.nan # peak rain rate during the AR event (GEFS)
    duration_df['ASOS_prec_accum'] = np.nan # total accumulated precipitation (ASOS)
    duration_df['ASOS_prec_max_rate'] = np.nan # peak rain rate during the AR event (ASOS)
    duration_df['ARI_1hr'] = np.nan # 1 hr ARI based on Atlas 14 and ASOS prec
    duration_df['ARI_3hr'] = np.nan # 3 hr ARI based on Atlas 14 and ASOS prec
    duration_df['ARI_6hr'] = np.nan # 6 hr ARI based on Atlas 14 and ASOS prec
    duration_df['ARI_12hr'] = np.nan # 12 hr ARI based on Atlas 14 and ASOS prec
    duration_df['ARI_24hr'] = np.nan # 24 hr ARI based on Atlas 14 and ASOS prec
    duration_df['impact_scale'] = np.nan # AR impact scale assigned by Aaron
    duration_df['impacts'] = np.nan # 0 or 1 depending on if Aaron has an impact in database at that station
    duration_df['impact_notes'] = np.nan # copies description of impacts over
    
    return duration_df

def AR_rank(ds):
    """
    Super simple AR rank determiner based on Ralph et al., 2019. 
    This ranks the AR based on the duration of AR conditions and maximum IVT during the AR.
    Really only works if you know the start and stop of each AR
    
    Parameters
    ----------
    ds : 
        xarray dataset with ivt
    
    Returns
    -------
    rank : int
        AR rank
    
    Notes
    -----
    - This currently only functions with 3-hourly data.
    
    """    
    # get AR preliminary rank
    max_IVT = ds.ivt.max()
    
    if (max_IVT >= 250.) & (max_IVT < 500.):
        prelim_rank = 1
    elif (max_IVT >= 500.) & (max_IVT < 750.):
        prelim_rank = 2
    elif (max_IVT >= 750.) & (max_IVT < 1000.):
        prelim_rank = 3
    elif (max_IVT >= 1000.) & (max_IVT < 1250.):
        prelim_rank = 4
    elif (max_IVT >= 1250):
        prelim_rank = 5
    else:
        prelim_rank = np.nan()
        
        
    # get maximum AR duration with IVT >=250 kg m-1 s-1
    duration = xr.where(ds.ivt >= 250, 3, 0).sum().values # where IVT exceeds 250, put in 3 (hours), otherwise 0
    
    if duration >= 48:
        rank = prelim_rank + 1
    elif duration < 24:
        rank = prelim_rank - 1
    else: 
        rank = prelim_rank
        
    return rank


def preprocess_IVT_info(stationID, ARID, df):
    '''
    For the given ASOS station location and AR track ID, calculate:
        - the maximum IVT value during the AR
        - the IVT direction at the time of peak IVT
        - the AR Scale value
        - the time of peak IVT
    '''
    # import configuration file for station information
    yaml_doc = '../data/ASOS_station_info.yml'
    config = yaml.load(open(yaml_doc), Loader=yaml.SafeLoader)
    ASOS_dict = config[stationID]
    
    ## open the IVT dataset
    path_to_data = '/cw3e/mead/projects/cwp140/scratch/dnash/data/' 
    fname = path_to_data + 'preprocessed/GEFSv12_reforecast/ivt/{0}_ivt.nc'.format(ARID)
    ds = xr.open_dataset(fname)
    # Convert DataArray longitude coordinates from -180-179 to 0-359
    ds = ds.assign_coords({"lon": ds.lon % 360})

    ## select the grid closest to the station
    ts = ds.sel(lat=ASOS_dict['lat'], lon=ASOS_dict['lon'] % 360, method='nearest')

    ## IVT max
    df.loc[ARID, 'IVT_max'] = ts.ivt.max().values
    time_idx = ts.ivt.argmax(dim='time').values
    max_IVT_time = ts.isel(time=time_idx).time.values
    df.loc[ARID, 'IVT_max_time'] = max_IVT_time

    ## AR Scale
    df.loc[ARID, 'ar_scale'] = AR_rank(ts)

    ## IVT direction
    ## pull IVT and IVTDIR where ivt is max
    event_max = ts.sel(time=max_IVT_time)
    uvec = event_max.ivtu.values
    uvec = units.Quantity(uvec, "m/s")
    vvec = event_max.ivtv.values
    vvec = units.Quantity(vvec, "m/s")
    df.loc[ARID, 'IVT_dir'] = mpcalc.wind_direction(uvec, vvec)

    return df

def preprocess_freezing_level(stationID, ARID, df):
    '''
    For the given ASOS station location and AR track ID, calculate:
        - freezing level at the time of peak IVT
    '''
    # import configuration file for station information
    yaml_doc = '../data/ASOS_station_info.yml'
    config = yaml.load(open(yaml_doc), Loader=yaml.SafeLoader)
    ASOS_dict = config[stationID]
    
    ## open the prec dataset
    path_to_data = '/cw3e/mead/projects/cwp140/scratch/dnash/data/' 
    fname = path_to_data + 'preprocessed/GEFSv12_reforecast/freezing_level/{0}_freezing_level.nc'.format(ARID)
    ds = xr.open_dataset(fname)
    # Convert DataArray longitude coordinates from -180-179 to 0-359
    ds = ds.assign_coords({"lon": ds.lon % 360})

    ## select the grid closest to the station
    ts = ds.sel(lat=ASOS_dict['lat'], lon=ASOS_dict['lon'] % 360, method='nearest')

    ## subset to start and end dates of AR event
    max_IVT_time = df.loc[ARID, 'IVT_max_time']
    ts = ts.sel(time=max_IVT_time)

    df.loc[ARID, 'freezing_level'] = ts.freezing_level.values # freezing level at the time of peak IVT

    return df

def preprocess_prec_GEFS(stationID, ARID, df):
    '''
    For the given ASOS station location and AR track ID, calculate:
        - the total accumulated precipitation
        - the peak precipitation intensity (3-hourly)
    '''
    # import configuration file for station information
    yaml_doc = '../data/ASOS_station_info.yml'
    config = yaml.load(open(yaml_doc), Loader=yaml.SafeLoader)
    ASOS_dict = config[stationID]
    
    ## open the prec dataset
    path_to_data = '/cw3e/mead/projects/cwp140/scratch/dnash/data/' 
    fname = path_to_data + 'preprocessed/GEFSv12_reforecast/prec/{0}_prec.nc'.format(ARID)
    ds = xr.open_dataset(fname)
    # Convert DataArray longitude coordinates from -180-179 to 0-359
    ds = ds.assign_coords({"lon": ds.lon % 360})

    ## select the grid closest to the station
    ts = ds.sel(lat=ASOS_dict['lat'], lon=ASOS_dict['lon'] % 360, method='nearest')

    ## subset to start and end dates of AR event
    start_date = df.loc[ARID, 'start_date']
    end_date = df.loc[ARID, 'end_date']
    ts = ts.sel(time=slice(start_date, end_date))

    df.loc[ARID, 'GFS_prec_accum'] = ts.tp.sum().values # total accumulated precipitation
    df.loc[ARID, 'GFS_prec_max_rate'] = ts.tp.max().values # peak 3-hour precip intensity

    return df