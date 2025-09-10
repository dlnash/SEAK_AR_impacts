#!/bin/bash
######################################################################
# Filename:    copy_figs_to_skyriver.sh
# Author:      Deanna Nash dnash@ucsd.edu
# Description: Script to copy M-Climate historical images to skyriver for web tool
#
######################################################################

PATH_TO_DATA="/cw3e/mead/projects/cwp140/data/mclimate_images/"
PATH_TO_MERCED="dnash@skyriver.ucsd.edu:/data/projects/website/mirror/htdocs/Projects/MClimate/images/images_historical/"

given_dates=(
"20051122"
# "20201202"
# "20240923"
"20150818"
"20231120"
)

for given_date in "${given_dates[@]}"
do
    echo "Given date: $given_date"
    for i in {1..7}
    do
        d=$(date -d "${given_date} - $i day" +%Y%m%d)
        echo "  $d"
        SRC_DIR="${PATH_TO_DATA}mclimate_${d}/"
        DEST="${PATH_TO_MERCED}${given_date}/mclimate_${d}/"
        ls -al $SRC_DIR
        echo "source is $SRC_DIR"
        echo "destination is $DEST"
        rsync -av "${SRC_DIR}" "${DEST}"
    
    done
done

