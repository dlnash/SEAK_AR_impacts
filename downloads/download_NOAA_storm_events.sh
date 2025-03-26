#!/bin/bash
######################################################################
# Filename:    download_NOAA_storm_events.sh
# Author:      Deanna Nash dnash@ucsd.edu
# Description: Script to download and unpack NOAA storm events database
#
######################################################################
DATADIR='/expanse/nfs/cw3e/cwp140/downloads/noaastormevents/'
WEBLINK='https://www.ncei.noaa.gov/pub/data/swdi/stormevents/csvfiles/'
## NOTE: YOU MAY NEED TO UPDATE THIS IF THE FILES HAVE RECENTLY BEEN UPDATED
filelst=(
StormEvents_details-ftp_v1.0_d2000_c20220425.csv.gz 
StormEvents_details-ftp_v1.0_d2001_c20220425.csv.gz	 
StormEvents_details-ftp_v1.0_d2002_c20220425.csv.gz	 
StormEvents_details-ftp_v1.0_d2003_c20220425.csv.gz	 
StormEvents_details-ftp_v1.0_d2004_c20220425.csv.gz	 
StormEvents_details-ftp_v1.0_d2005_c20220425.csv.gz	 
StormEvents_details-ftp_v1.0_d2006_c20250122.csv.gz	 
StormEvents_details-ftp_v1.0_d2007_c20240216.csv.gz 
StormEvents_details-ftp_v1.0_d2008_c20240620.csv.gz
StormEvents_details-ftp_v1.0_d2009_c20231116.csv.gz	 
StormEvents_details-ftp_v1.0_d2010_c20220425.csv.gz
StormEvents_details-ftp_v1.0_d2011_c20230417.csv.gz 
StormEvents_details-ftp_v1.0_d2012_c20221216.csv.gz
StormEvents_details-ftp_v1.0_d2013_c20230118.csv.gz	 
StormEvents_details-ftp_v1.0_d2014_c20231116.csv.gz 
StormEvents_details-ftp_v1.0_d2015_c20240716.csv.gz	 
StormEvents_details-ftp_v1.0_d2016_c20220719.csv.gz	 
StormEvents_details-ftp_v1.0_d2017_c20250122.csv.gz	 
StormEvents_details-ftp_v1.0_d2018_c20240716.csv.gz	 
StormEvents_details-ftp_v1.0_d2019_c20240117.csv.gz 
StormEvents_details-ftp_v1.0_d2020_c20240620.csv.gz	 
StormEvents_details-ftp_v1.0_d2021_c20240716.csv.gz 
StormEvents_details-ftp_v1.0_d2022_c20241121.csv.gz
StormEvents_details-ftp_v1.0_d2023_c20250317.csv.gz 
StormEvents_details-ftp_v1.0_d2024_c20250317.csv.gz
)

# now loop through each filename to download and unpack the data
for i in ${!filelst[*]}
do
    cd ${DATADIR}
    infile="${WEBLINK}${filelst[$i]}"
    wget ${infile}
    gunzip ${filelst[$i]}
done