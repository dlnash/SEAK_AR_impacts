"""
Filename:    custom_cmaps.py
Author:      Deanna Nash, dnash@ucsd.edu
Description: Functions for custom cmaps adapted from from https://github.com/samwisehawkins/nclcmaps
"""

import numpy as np
import matplotlib.colors as mcolors
from matplotlib.colors import ListedColormap

__all__ = ['custom_cmaps']

colors = {"mclimate": [[1.000, 1.000, 0.898], # 0. - 75
                            [0.969, 0.988, 0.725], # 75 - 90
                            [0.851, 0.941, 0.639], # 90 - 95
                            [0.678, 0.867, 0.557], # 95 - 97
                            [0.471, 0.776, 0.475], # 97 - 99
                            [0.255, 0.671, 0.365], # 99 - 99.5
                            [0.137, 0.518, 0.263], # 99.5 - 99.8
                            [0.000, 0.408, 0.216], # 99.8 - 99.9
                            [0.000, 0.271, 0.161]] # 99.9 - 100.
         }

bounds = {"mclimate": [0., 75., 90., 95., 97., 99., 99.5, 99.8, 99.9, 100.]}

def cmap(name):
    data = np.array(colors[name])
    data = data / np.max(data)
    cmap = ListedColormap(data, name=name)
    bnds = bounds[name]
    norm = mcolors.BoundaryNorm(bnds, cmap.N)
    return cmap, norm, bnds