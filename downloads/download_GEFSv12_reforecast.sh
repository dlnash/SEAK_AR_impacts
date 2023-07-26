#!/bin/bash
######################################################################
# Filename:    download_GEFSv12_reforecast.sh
# Author:      Deanna Nash dnash@ucsd.edu
# Description: Script to download GEFSv12 reforecast data
# https://registry.opendata.aws/noaa-gefs-reforecast/ (data link)
#
######################################################################

### Inputs (TODO: later set this up with a python script to use normalized start and end dates from the AR duration database)
YR='2015' #2015-08-17 06:00 to 2015-08-19 06:00

datelst=(
'20150817'
'20150818'
'20150819'
)

ARID='201508151811' # AR track ID

### Variables to download:
var_array=(
apcp_sfc ## Total Precipitation 
ugrd_pres ## U below 700 mb
ugrd_pres_abv700mb ## U above 700 mb
vgrd_pres ## V below 700 mb
vgrd_pres_abv700mb ## V above 700 mb
tmp_pres ## T below 700 mb
tmp_pres_abv700mb ## T above 700 mb
spfh_pres ## Q below 700 mb
spfh_pres_abv700mb ## Q above 700 mb
hgt_pres ## Z below 700 mb
hgt_pres_abv700mb ## Z above 700 mb
)

## outer loop - loop through start date to end date
for i in ${!datelst[*]}
do 
    IN_DATE="${datelst[$i]}"
    
    ### Set up paths
    PATH_TO_DATA='s3://noaa-gefs-retrospective/GEFSv12/reforecast/${YR}/${IN_DATE}00/c00/Days:1-10/'
    PATH_TO_OUT='/cw3e/mead/projects/cwp140/scratch/dnash/data/downloads/GEFSv12_reforecast/${ARID}/'
    mkdir ${PATH_TO_OUT}

    ## inner loop - loop through variables
    
    for j in ${!var_array[*]}
    do
        VAR_NAME="${var_array[$j]}"
    
        ### Copy a single file from S3 to local

        INPUT_FNAME='${PATH_TO_DATA}${VAR_NAME}_${IN_DATE}00_c00.grib2'
        OUTPUT_FNAME='${PATH_TO_OUT}${VAR_NAME}_${IN_DATE}00_c00.grib2'

        aws s3 cp ${INPUT_FNAME} ${OUTPUT_FNAME} --no-sign-request
    
    done

done
