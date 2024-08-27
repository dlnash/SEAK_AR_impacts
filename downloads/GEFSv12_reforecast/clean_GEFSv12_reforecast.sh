#!/bin/bash
######################################################################
# Filename:    clean_GEFSv12_reforecast.sh
# Author:      Deanna Nash dnash@ucsd.edu
# Description: Script to remove GEFSv12 reforecast data after preprocessed
# https://registry.opendata.aws/noaa-gefs-reforecast/ (data link)
#
######################################################################

### Inputs

ARID=${1}
VARNAME=${2}

## remove the downloaded GEFSv12 reforecast data
PATH_TO_DATA="/cw3e/mead/projects/cwp140/scratch/dnash/data/downloads/GEFSv12_reforecast/${VARNAME}/${ARID}/"
rm -rf ${PATH_TO_DATA}

## remove the text files with the list of dates to download
PATH_TO_DATA="/cw3e/mead/projects/cwp140/scratch/dnash/repos/SEAK_AR_impacts/out/${VARNAME}/${ARID}_*.txt"
rm -rf ${PATH_TO_DATA}

