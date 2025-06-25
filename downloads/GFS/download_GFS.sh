#!/bin/bash
######################################################################
# Filename:    download_GFS.sh
# Author:      Deanna Nash dnash@ucsd.edu
# Description: Script to download GFS data
# https://registry.opendata.aws/noaa-gfs-bdp-pds/ (data link)
#
######################################################################

### Inputs
INIT_DATE=$1
DATA_NAME=$2

### Set up paths
PATH_TO_OUT="/expanse/lustre/scratch/dnash/temp_project/downloaded/GFS/${INIT_DATE}/"
PATH_TO_DATA="s3://noaa-gfs-bdp-pds/gfs.${INIT_DATE}/00/atmos/"

lead_array=($(seq -f "%03g" 3 3 168)) ## every F from 3-168 every 3 hours

## outer loop - loop through ensemble members
for i in ${!lead_array[*]}
do
    LEAD="${lead_array[$i]}"
    FNAME="gfs.t00z.${DATA_NAME}.0p25.f${LEAD}"
    INPUT_FNAME="${PATH_TO_DATA}${FNAME}"
    OUTPUT_FNAME="${PATH_TO_OUT}${FNAME}"
    # echo ${OUTPUT_FNAME}
    /expanse/nfs/cw3e/cwp140/aws/local/bin/aws s3 cp --region us-east-1 ${INPUT_FNAME} ${OUTPUT_FNAME} --no-sign-request

done
