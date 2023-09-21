"""
Filename:    preprocess_df_funcs.py
Author:      Deanna Nash, dnash@ucsd.edu
Description: Pull IVT, precip, and freezing level info for each AR event in Southeast Alaska
"""

def build_empty_df(stationID):
    ## read AR duration file
    duration_df = pd.read_csv(path_to_out + 'AR_track_duration_SEAK.csv')
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