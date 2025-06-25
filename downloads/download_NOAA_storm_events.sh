#!/bin/bash
######################################################################
# Filename:    download_NOAA_storm_events.sh
# Author:      Deanna Nash dnash@ucsd.edu
# Description: Script to download and unpack NOAA storm events database
#
######################################################################
DATADIR='/expanse/nfs/cw3e/cwp140/downloads/noaastormevents/'
cd ${DATADIR}

curl -sl ftp://ftp.ncei.noaa.gov/pub/data/swdi/stormevents/csvfiles/ | grep 'StormEvents_details-ftp_.*.csv.gz' > file_list.txt
while read file; do
  wget ftp://ftp.ncei.noaa.gov/pub/data/swdi/stormevents/csvfiles/"$file"
  gunzip ${file}
done < file_list.txt