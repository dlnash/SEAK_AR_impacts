#!/bin/bash
######################################################################
# Filename:    download_GEFS.sh
# Author:      Deanna Nash dnash@ucsd.edu
# Description: Script to download GEFS data
# https://registry.opendata.aws/noaa-gefs-pds/ (data link)
#
######################################################################

### Inputs
INIT_DATE=$1
DATA_NAME=$2
LEAD=$3
ENS=$4

### Set up paths
PATH_TO_OUT="/expanse/lustre/scratch/dnash/temp_project/downloaded/GEFS/${INIT_DATE}/"
PATH_TO_DATA="s3://noaa-gefs-pds/gefs.${INIT_DATE}/00/atmos/${DATA_NAME}p5/"

INPUT_FNAME="${PATH_TO_DATA}${ENS}.t00z.${DATA_NAME}.0p50.f${LEAD}"
OUTPUT_FNAME="${PATH_TO_OUT}${ENS}.t00z.${DATA_NAME}.0p50.f${LEAD}"
# echo ${OUTPUT_FNAME}
/expanse/nfs/cw3e/cwp140/aws/local/bin/aws s3 cp --region us-east-1 ${INPUT_FNAME} ${OUTPUT_FNAME} --no-sign-request