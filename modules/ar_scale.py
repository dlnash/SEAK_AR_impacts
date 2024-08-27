#!/usr/bin/python3
"""
Filename:    ar_scale.py
Author:      Deanna Nash, dnash@ucsd.edu
Description: python class for calculating the AR scale using a pandas dataframe with IVT and dates

To implement:
    from ar_scale import calc_ar_scale
    ar_scale = calc_ar_scale(df)
    
    where df is a pandas dataframe with IVT magnitude (kg m-1 s-1) and dates (datetime dtype)
    and temp_res is the temporal resolution of the time series in hours
"""

import xarray as xr
import pandas as pd
import numpy as np
from itertools import groupby


def find_prelim_rank(df):

    if (df['IVT'] >= 250.) & (df['IVT'] < 500.):
        prelim_rank = 1
    elif (df['IVT']>= 500.) & (df['IVT'] < 750.):
        prelim_rank = 2
    elif (df['IVT'] >= 750.) & (df['IVT'] < 1000.):
        prelim_rank = 3
    elif (df['IVT'] >= 1000.) & (df['IVT'] < 1250.):
        prelim_rank = 4
    elif (df['IVT'] >= 1250):
        prelim_rank= 5
    else:
        prelim_rank = 0


    return prelim_rank

def find_IVT_exceed_250(df):

    if df['IVT'] >= 250:
        AR = 1
    else:
        AR = 0

    return AR

def calc_duration(df):
    # get the temporal resolution in hours
    t = df['date'].iloc[1] - df['date'].iloc[0]
    nhrs = t.seconds/3600. # divide by 3600 to convert seconds to hours

    a = df['AR'] != 0 # this will place True for all rows where AR is not 0
    tmp = a.cumsum()-a.cumsum().where(~a).ffill().fillna(0).astype(int) # cumulative sum where not 0

    duration = tmp.values*nhrs # get duration values in number of hours

    return duration

def calc_idx_lst(df):
    a = df['AR'] != 0 # this will place True for all rows where AR is not 0
    ## this grabs the start and stop indices of each AR
    x = a.values
    idx = [(group[0], group[-1]) for group in (
     list(group) for key, group in groupby(range(len(x)), key=x.__getitem__) if key)]

    return idx

def final_AR_rank(duration, prelim_rank):   
    if duration >= 48:
            rank = prelim_rank + 1
    elif duration < 24:
        rank = prelim_rank - 1
    else: 
        rank = prelim_rank

    return rank

def build_ar_scale_df(df):
    idx_lst = calc_idx_lst(df)

    start_lst = []
    end_lst = []
    dur_lst = []
    rank_lst = []
    max_IVT = []

    for i, idx in enumerate(idx_lst):

        start_lst.append(df['date'].iloc[idx[0]]) # get the start date of the AR
        end_lst.append(df['date'].iloc[idx[1]]) # get the end date of the AR
        dur = df['duration'].iloc[idx[0]:idx[1]].max()
        max_IVT.append(df['IVT'].iloc[idx[0]:idx[1]].max())
        prelim_rank = df['prelim_rank'].iloc[idx[0]:idx[1]].max()
        dur_lst.append(dur) # get the duration of the AR
        rank_lst.append(final_AR_rank(dur, prelim_rank)) # get the final AR rank

    ## build new dateframe with start date, stop date, duration, max IVT, and AR scale
    d = {'start_date': start_lst, 'end_date': end_lst, 'duration': dur_lst, 'max_IVT': max_IVT, 'AR_scale': rank_lst}
    final_df = pd.DataFrame(data=d)
    final_df = final_df.dropna(subset=['AR_scale']) # drop rows where AR scale is NAN
    final_df = final_df[final_df['AR_scale'] != 0] # drop rows where AR scale is 0

    return final_df

def calc_ar_scale(df):
    '''
    Returns a Pandas dataframe with AR event start date, stop date, duration, maximum IVT, and Ralph et al. (2019) AR scale 
    
    Parameters
    ----------
    df : pandas dataframe
        A pandas dataframe with columns "date" and "IVT"
        "date" should be datetime dtype
        "IVT" should be float IVT magnitude (kg m-1 s-1) 
  
    Returns
    -------
    new_df : pandas dataframe
        A pandas dataframe with AR event start date, stop date, duration, maximum IVT, and Ralph et al. (2019) AR scale
    
    '''
        
    df['prelim_rank'] = df.apply(find_prelim_rank, axis=1)
    df['AR'] = df.apply(find_IVT_exceed_250, axis=1)
    df['duration'] = calc_duration(df)

    new_df = build_ar_scale_df(df)

    return new_df