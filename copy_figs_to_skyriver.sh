#!/bin/bash
######################################################################
# Filename:    copy_figs_to_skyriver.sh
# Author:      Deanna Nash dnash@ucsd.edu
# Description: Script to copy M-Climate historical images to skyriver for web tool
#
######################################################################

### Inputs
array=(
20051122
20201202
20240923
20150818
20231120
)

## outer loop - loop through ensemble members
for i in ${!array[*]}
do
    EVENT="${array[$i]}"
    rsync -av --exclude '*.csv' /expanse/nfs/cw3e/cwp140/images_historical/${EVENT} dnash@skyriver.ucsd.edu:/data/projects/website/mirror/htdocs/Projects/MClimate/images/images_historical

done

exit
