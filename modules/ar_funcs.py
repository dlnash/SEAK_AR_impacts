"""
Filename:    ar_funcs.py
Author:      Deanna Nash, dnash@ucsd.edu
Description: Functions for getting AR metrics
"""

# Import Python modules
import os, sys
import yaml
import glob
import numpy as np
import xarray as xr
import pandas as pd
from itertools import groupby
import metpy.calc as mpcalc
from metpy.units import units
from scipy.integrate import trapz
from pandas.tseries.offsets import MonthEnd


## FUNCTIONS

def clean_impact_data(start_date = '2000-01-01', end_date = '2019-08-31'):
    fname = '../data/ar_impact_info.csv'
    impact_df = pd.read_csv(fname)
    impact_df = impact_df.set_index(pd.to_datetime(impact_df['Impact dates']))
    idx = (impact_df.index >= start_date) & (impact_df.index <= end_date)
    impact_df = impact_df.loc[idx]
    ## fix names of stations to match ASOS/COOP station ID
    ## we chose HONA2 OVER COOPHOOA2 because it had a longer period of record and also hourly data
    ## we chose PAJN over JNEA2 because it had a longer period of record
    ## choose PAHN for Haines over COOPAHNA2 bc it had a longer period of record and only daily data
    impact_df['Location'] = impact_df['Location'].replace({'JNNA2': 'PAJN', 'PECA2': 'COOPPECA2', 
                            'HCSA2': 'COOPHCSA2', 'AHNA2': 'PAHN',
                            'Thorne Bay': 'PAKW', 'Thorne Bay/PAKW': 'PAKW',
                            'Staney/PAKW': 'PAKW', 'HOOA2': 'HONA2',
                            np.nan: 'PAJN'})
    ## drop Pelican events bc they are the same as many other communities
    ## also Pelican station does not have precip info for this event
    impact_df = impact_df[impact_df['Location'] != 'COOPPECA2'] 
    
    return impact_df

def add_impact_info(stationIDX, stationID):
    
    test = impact_df.loc[(impact_df['Location'] == stationID)]
    ## current station df
    subset_df = df_lst[stationIDX]
    subset_df['impact_type'] = np.nan # type of impact
    subset_df['misc'] = np.nan # copies other notes over
        
    ar_impact = []
    for idx_impact, row_impact in test.iterrows():
        year = idx_impact.year
        month = idx_impact.month

        ## subset to year/month of current row in impact dataframe +- 15 days
        start = pd.to_datetime('{0}-{1}-01'.format(year, month)) - pd.DateOffset(days=15)
        end = pd.to_datetime('{0}-{1}'.format(idx_impact.year, idx_impact.month), format="%Y-%m") + MonthEnd(0, normalize=True) + pd.DateOffset(days=15)
        idx = (subset_df['start_date'] >= start) & (subset_df['end_date'] <= end)
        tmp = subset_df.loc[idx]

        for index, row in tmp.iterrows():
            date1 = row['start_date'] - pd.DateOffset(hours=24)
            date2 = row['end_date'] + pd.DateOffset(hours=24)

            if date1 <= idx_impact <= date2:
                # print(date1, date2, impact_date, index, "PASS!")
                ar_impact.append(idx_impact)
                subset_df.loc[index, 'impact_scale'] = row_impact['Impact Level']
                subset_df.loc[index, 'impacts'] = 1
                subset_df.loc[index, 'impact_type'] = row_impact['Impact']
                subset_df.loc[index, 'impact_notes'] = row_impact['Impact Information']
                subset_df.loc[index, 'misc'] = row_impact['Notes']
            else:
                pass
    ## get the impact dates not found in AR database        
    a = ar_impact
    b = test.index
    ar_not_found = set(a) ^ set(b)
                
    return subset_df, ar_not_found

def get_new_start(value):
    s = str(int(value))
    new_date = pd.to_datetime(s[:10], format='%Y%m%d%H')
    
    return new_date

def build_empty_df(stationID):
    ## read AR duration file
    duration_df = pd.read_csv('../out/AR_track_duration_SEAK.csv')
    # duration_df['start_date'] = pd.to_datetime(duration_df['start_date'])
    duration_df['start_date'] = duration_df['trackID'].map(get_new_start)
    duration_df['end_date'] = pd.to_datetime(duration_df['end_date'])
    duration_df.index = duration_df['trackID']
    
    ## build out the dataframe with the information we want to add
    # add empty columns
    duration_df['IVT_max'] = np.nan # maximum IVT during the AR event
    duration_df['IVT_max_time'] = np.nan # timestamp of maximum IVT during the AR event
    duration_df['IVT_dir'] = np.nan # IVT direction at the time of peak IVT
    duration_df['tIVT'] = np.nan # time-integrated IVT for the 7 days prior to start of storm, plus duration of storm
    duration_df['freezing_level'] = np.nan # freezing level at the time of peak IVT
    duration_df['ar_scale'] = np.nan # calculated AR scale based on GEFS 
    duration_df['GFS_prec_accum'] = np.nan # total accumulated precipitation (GEFS)
    duration_df['GFS_prec_max_rate'] = np.nan # peak rain rate during the AR event (GEFS)
    duration_df['ASOS_prec_accum'] = np.nan # total accumulated precipitation (ASOS)
    duration_df['ASOS_1hr'] = np.nan # 1 hr ARI based on Atlas 14 and ASOS prec
    duration_df['ASOS_3hr'] = np.nan # 3 hr ARI based on Atlas 14 and ASOS prec
    duration_df['ASOS_6hr'] = np.nan # 6 hr ARI based on Atlas 14 and ASOS prec
    duration_df['ASOS_12hr'] = np.nan # 12 hr ARI based on Atlas 14 and ASOS prec
    duration_df['ASOS_24hr'] = np.nan # 24 hr ARI based on Atlas 14 and ASOS prec
    duration_df['impact_scale'] = np.nan # AR impact scale assigned by Aaron
    duration_df['impacts'] = 0 # 0 or 1 depending on if Aaron has an impact in database at that station
    duration_df['impact_notes'] = np.nan # copies description of impacts over
    duration_df['impact_type'] = np.nan # type of impact
    duration_df['misc'] = np.nan # copies other notes over
    
    return duration_df

def read_mesowest_prec_data(stationID):
    fname = glob.glob('/home/dnash/comet_data/downloads/mesowest/{0}.*.csv'.format(stationID))
    skip_lst = np.arange(0, 10).tolist()
    skip_lst.append(11)
    prec_df = pd.read_csv(fname[0], skiprows=skip_lst, header=0)
    prec_df['date_time'] = pd.to_datetime(prec_df['Date_Time']).dt.tz_localize(None)
    prec_df = prec_df.set_index(['date_time'])
    
    if 'precip_accum_one_hour_set_1' in prec_df.columns:

        prec_df['prec_1h'] = prec_df['precip_accum_one_hour_set_1']
    elif 'precip_accum_set_1' in prec_df.columns:

        prec_df['prec_1h'] = prec_df['precip_accum_set_1'].diff()   
    elif 'precip_accum_24_hour_set_1' in prec_df.columns:

        ## get daily values, then divide by 24 for each hour within that day
        prec_df['prec_1h'] =  prec_df['precip_accum_24_hour_set_1'].dropna().resample('1H').ffill()/24.
    
    return prec_df

def preprocess_mesowest_precip(ARID, prec_df_lst, df_lst, start_date, end_date): 
    df_final = []
    for i, (prec_df, df) in enumerate(zip(prec_df_lst, df_lst)):
        # print(prec_df['Station_ID'].iloc[0])
        ## loop through each row in the AR duration df
        idx = (prec_df.index >= start_date) & (prec_df.index <= end_date)
        tmp = prec_df.loc[idx]

        ## pull out the total accumulated preciptiation
        accum_prec = tmp['prec_1h'].sum()
        # print('... Total accumulated precip...', accum_prec)
        ## pull peak 1h precip rate for duration of event
        peak_1hr = tmp['prec_1h'].max()
        # print('... 1 hr max precip...', peak_1hr)
        ## pull peak 3h precip rate for duration of event
        peak_3hr = tmp['prec_1h'].resample('3H').sum().max()
        # print('... 3 hr max precip...', peak_3hr)
        ## pull peak 6h precip rate for duration of event
        peak_6hr = tmp['prec_1h'].resample('6H').sum().max()
        # print('... 6 hr max precip...', peak_6hr)
        ## pull peak 12h precip rate for duration of event
        peak_12hr = tmp['prec_1h'].resample('12H').sum().max()
        # print('... 12 hr max precip...', peak_12hr)
        ## pull peak 24h precip rate for duration of event
        peak_24hr = tmp['prec_1h'].resample('24H').sum().max()
        # print('... 24 hr max precip...', peak_24hr)
        
        df.loc[ARID, 'ASOS_prec_accum'] = accum_prec # total accumulated precipitation (ASOS)
        df.loc[ARID, 'ASOS_1hr'] = peak_1hr # 1 hr ARI based on Atlas 14 and ASOS prec
        df.loc[ARID, 'ASOS_3hr'] = peak_3hr # 3 hr ARI based on Atlas 14 and ASOS prec
        df.loc[ARID, 'ASOS_6hr'] = peak_6hr # 6 hr ARI based on Atlas 14 and ASOS prec
        df.loc[ARID, 'ASOS_12hr'] = peak_12hr # 12 hr ARI based on Atlas 14 and ASOS prec
        df.loc[ARID, 'ASOS_24hr'] = peak_24hr # 24 hr ARI based on Atlas 14 and ASOS prec
        
        df_final.append(df)
        
    return df_final

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
        prelim_rank = np.nan
        
        
    # get maximum AR duration with IVT >=250 kg m-1 s-1
    duration = xr.where(ds.ivt >= 250, 3, 0).sum().values # where IVT exceeds 250, put in 3 (hours), otherwise 0
    
    if duration >= 48:
        rank = prelim_rank + 1
    elif duration < 24:
        rank = prelim_rank - 1
    else: 
        rank = prelim_rank
        
    return rank

def calc_time_integrated_IVT(ds):
    """
    Calculates time-integrated IVT using an xarray dataset that has IVTv and IVTu
    
    Parameters
    ----------
    ds : 
        xarray dataset with meridional and zonal IVT (ivtu, ivtv)
    
    Returns
    -------
    tIVT : xarray dataset
        xarray dataset with time-integrated IVT where the units are kg m-1 divided by a factor of 10^7

    """ 
    # time integrate IVT
    time = np.arange(0, (len(ds.time)*3), 3)*3600 # convert to seconds
    tIVTu = trapz(y=ds.ivtu.values, x=time, axis=0)
    tIVTv = trapz(y=ds.ivtv.values, x=time, axis=0)
    tIVT = np.sqrt(tIVTu**2 + tIVTv**2)
    
    return tIVT

def read_GEFSv12_reforecast_data(varname, ARID):
    
    ## open the dataset
    path_to_data = '/data/projects/Comet/cwp140/' 
    fname = path_to_data + 'preprocessed/GEFSv12_reforecast/{0}/{1}_{0}.nc'.format(varname, ARID)
    ds = xr.open_dataset(fname)
    # Convert DataArray longitude coordinates from -180-179 to 0-359
    ds = ds.assign_coords({"longitude": ds.lon % 360})
    
    if varname == 'ivt':
        tIVT = calc_time_integrated_IVT(ds)
        ds = ds.assign(tIVT=(['lat', 'lon'], tIVT))
    else: pass
    
    return ds


def preprocess_IVT_info(config, ds, ARID, df_lst):
    '''
    For the given ASOS station location and AR track ID, calculate:
        - the maximum IVT value during the AR
        - the IVT direction at the time of peak IVT
        - the AR Scale value
        - the time of peak IVT
    '''   
    
    ## loop through all the stations
    df_final = []
    for i, (stationID, df) in enumerate(zip(config, df_lst)):

        ## select the grid closest to the station
        lat = float(config[stationID]['lat'])
        lon = float(config[stationID]['lon']) % 360
        ts = ds.sel(lat=lat, lon=lon, method='nearest')
        
        ## subset to start and end dates of AR event
        start_date = df.loc[ARID, 'start_date']
        end_date = df.loc[ARID, 'end_date']
        ts = ts.sel(time=slice(start_date, end_date))

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
        
        ## tIVT
        df.loc[ARID, 'tIVT'] = ts.tIVT.values

        df_final.append(df)

    return df_final

def preprocess_freezing_level(config, ds, ARID, df_lst):
    '''
    For the given ASOS station location and AR track ID, calculate:
        - freezing level at the time of peak IVT
    '''
    ## loop through all the stations
    df_final = []
    for i, (stationID, df) in enumerate(zip(config, df_lst)):
        ## select the grid closest to the station
        lat = float(config[stationID]['lat'])
        lon = float(config[stationID]['lon']) % 360
        ts = ds.sel(lat=lat, lon=lon, method='nearest')

        ## subset to start and end dates of AR event
        max_IVT_time = df.loc[ARID, 'IVT_max_time']
        ts = ts.sel(time=max_IVT_time)

        df.loc[ARID, 'freezing_level'] = ts.freezing_level.values # freezing level at the time of peak IVT
        
        df_final.append(df)

    return df_final

def preprocess_prec_GEFS(config, ds, ARID, df_lst):
    '''
    For the given ASOS station location and AR track ID, calculate:
        - the total accumulated precipitation
        - the peak precipitation intensity (3-hourly)
    '''
    ## loop through all the stations
    df_final = []
    for i, (stationID, df) in enumerate(zip(config, df_lst)):
        ## select the grid closest to the station
        lat = float(config[stationID]['lat'])
        lon = float(config[stationID]['lon']) % 360
        ts = ds.sel(lat=lat, lon=lon, method='nearest')

        ## subset to start and end dates of AR event
        start_date = df.loc[ARID, 'start_date']
        end_date = df.loc[ARID, 'end_date']
        ts = ts.sel(time=slice(start_date, end_date))

        df.loc[ARID, 'GFS_prec_accum'] = ts.tp.sum().values # total accumulated precipitation
        df.loc[ARID, 'GFS_prec_max_rate'] = ts.tp.max().values # peak 3-hour precip intensity
        df_final.append(df)

    return df_final