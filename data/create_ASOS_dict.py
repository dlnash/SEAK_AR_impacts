"""
Filename:    create_ASOS_dict.py
Author:      Deanna Nash, dnash@ucsd.edu
Description: Functions for creating a .yaml file of dictionaries with ASOS station information
"""

import glob
import pandas as pd
import yaml
from itertools import chain

filenames = glob.glob('/home/dnash/comet_data/downloads/mesowest/*.csv')
d_lst = []

## read .csv files with ASOS station information, put into dictionary
for i, fi in enumerate(filenames):
    print(fi)
    prec_df = pd.read_csv(fi, nrows=8, skiprows=2, header=None, names=['primary', 'secondary'])
    # print(prec_df.iloc[3].values[0].split(' '))
    d = {prec_df.iloc[2].values[0].split(' ')[-1]:
        {'name': prec_df.iloc[3].values[0].split(' ')[3],
         'lat': prec_df.iloc[4].values[0].split(' ')[-1],
         'lon': prec_df.iloc[5].values[0].split(' ')[-1],
         'elev':prec_df.iloc[6].values[0].split(' ')[-1]}
        }
    d_lst.append(d)

## merge all the dictionaries to one
dest = dict(chain.from_iterable(map(dict.items, d_lst)))

## write to .yaml file and close
file=open("../data/ASOS_station_info_new.yaml","w")
yaml.dump(dest,file)
file.close()
print("YAML file saved.")