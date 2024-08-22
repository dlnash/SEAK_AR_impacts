"""
Filename:    plotter.py
Author:      Deanna Nash, dnash@ucsd.edu
Description: Functions for plotting
"""

# Import Python modules

import os, sys
import numpy as np
import itertools
import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
import matplotlib.ticker as mticker
import colorsys
from matplotlib.colors import LinearSegmentedColormap # Linear interpolation for color maps
import matplotlib.patches as mpatches
import matplotlib.animation as animation
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from matplotlib.projections import get_projection_class
import pandas as pd
from matplotlib.gridspec import GridSpec
from matplotlib.colorbar import Colorbar # different way to handle colorbar
import seaborn as sns
import cmocean.cm as cmo
from datetime import timedelta
import textwrap

# Import my modules
sys.path.append('../modules') # Path to modules
from constants import ucsd_colors
import custom_cmaps as ccmap

def plot_terrain(ax, ext):
    fname = '/expanse/nfs/cw3e/cwp140/downloads/ETOPO1_Bed_c_gmt4.grd'
    datacrs = ccrs.PlateCarree()
    grid = xr.open_dataset(fname)
    grid = grid.where(grid.z > 0) # mask below sea level
    grid = grid.sel(x=slice(ext[0], ext[1]), y=slice(ext[2], ext[3]))
    cs = ax.pcolormesh(grid.x, grid.y, grid.z,
                        cmap=cmo.gray_r, transform=datacrs, alpha=0.7)
    
    return ax
    
def draw_basemap(ax, datacrs=ccrs.PlateCarree(), extent=None, xticks=None, yticks=None, grid=False, left_lats=True, right_lats=False, bottom_lons=True, mask_ocean=False, coastline=True):
    """
    Creates and returns a background map on which to plot data. 
    
    Map features include continents and country borders.
    Option to set lat/lon tickmarks and draw gridlines.
    
    Parameters
    ----------
    ax : 
        plot Axes on which to draw the basemap
    
    datacrs : 
        crs that the data comes in (usually ccrs.PlateCarree())
        
    extent : float
        Set map extent to [lonmin, lonmax, latmin, latmax] 
        Default: None (uses global extent)
        
    grid : bool
        Whether to draw grid lines. Default: False
        
    xticks : float
        array of xtick locations (longitude tick marks)
    
    yticks : float
        array of ytick locations (latitude tick marks)
        
    left_lats : bool
        Whether to add latitude labels on the left side. Default: True
        
    right_lats : bool
        Whether to add latitude labels on the right side. Default: False
        
    Returns
    -------
    ax :
        plot Axes with Basemap
    
    Notes
    -----
    - Grayscale colors can be set using 0 (black) to 1 (white)
    - Alpha sets transparency (0 is transparent, 1 is solid)
    
    """
    ## some style dictionaries
    kw_ticklabels = {'size': 10, 'color': 'dimgray', 'weight': 'light'}
    kw_grid = {'linewidth': .5, 'color': 'k', 'linestyle': '--', 'alpha': 0.4}
    kw_ticks = {'length': 4, 'width': 0.5, 'pad': 2, 'color': 'black',
                         'labelsize': 10, 'labelcolor': 'dimgray'}

    # Use map projection (CRS) of the given Axes
    mapcrs = ax.projection    
    
    # Add map features (continents and country borders)
    ax.add_feature(cfeature.LAND, facecolor='0.9')      
    ax.add_feature(cfeature.BORDERS, edgecolor='0.4', linewidth=0.8)
    if coastline == True:
        ax.add_feature(cfeature.COASTLINE, edgecolor='0.4', linewidth=0.8)
    if mask_ocean == True:
        ax.add_feature(cfeature.OCEAN, edgecolor='0.4', zorder=12, facecolor='white') # mask ocean
        
    ## Tickmarks/Labels
    ## Add in meridian and parallels
    if mapcrs == ccrs.NorthPolarStereo():
        gl = ax.gridlines(draw_labels=False,
                      linewidth=.5, color='black', alpha=0.5, linestyle='--')
    elif mapcrs == ccrs.SouthPolarStereo():
        gl = ax.gridlines(draw_labels=False,
                      linewidth=.5, color='black', alpha=0.5, linestyle='--')
        
    else:
        gl = ax.gridlines(crs=datacrs, draw_labels=True, **kw_grid)
        gl.top_labels = False
        gl.left_labels = left_lats
        gl.right_labels = right_lats
        gl.bottom_labels = bottom_lons
        gl.xlocator = mticker.FixedLocator(xticks)
        gl.ylocator = mticker.FixedLocator(yticks)
        gl.xformatter = LONGITUDE_FORMATTER
        gl.yformatter = LATITUDE_FORMATTER
        gl.xlabel_style = kw_ticklabels
        gl.ylabel_style = kw_ticklabels
    
    ## Gridlines
    # Draw gridlines if requested
    if (grid == True):
        gl.xlines = True
        gl.ylines = True
    if (grid == False):
        gl.xlines = False
        gl.ylines = False
            

    # apply tick parameters
    ax.set_xticks(xticks, crs=datacrs)
    ax.set_yticks(yticks, crs=datacrs)
    plt.yticks(color='w', size=1) # hack: make the ytick labels white so the ticks show up but not the labels
    plt.xticks(color='w', size=1) # hack: make the ytick labels white so the ticks show up but not the labels
    ax.ticklabel_format(axis='both', style='plain')

    ## Map Extent
    # If no extent is given, use global extent
    if extent is None:        
        ax.set_global()
        extent = [-180., 180., -90., 90.]
    # If extent is given, set map extent to lat/lon bounding box
    else:
        ax.set_extent(extent, crs=datacrs)
    
    return ax

def plot_mclimate_forecast(ds, fc, step, varname, fname, ext=[-170., -120., 50., 75.]):
    ts = pd.to_datetime(ds.init_date.values, format="%Y%m%d%H") 
    init_date = ts.strftime('%Y%m%d%H')
    # Set up projection
    mapcrs = ccrs.PlateCarree()
    datacrs = ccrs.PlateCarree()
    
    # Set tick/grid locations
    lats = ds.lat.values
    lons = ds.lon.values
    dx = np.arange(lons.min().round(),lons.max().round()+10,10)
    dy = np.arange(lats.min().round(),lats.max().round()+10,10)
    
    # Create figure
    fig = plt.figure(figsize=(9.5, 6.25))
    fig.dpi = 300
    fmt = 'png'
    
    nrows = 3
    ncols = 1
    
    # contour labels
    kw_clabels = {'fontsize': 7, 'inline': True, 'inline_spacing': 7, 'fmt': '%i',
                  'rightside_up': True, 'use_clabeltext': True}
    
    kw_ticklabels = {'size': 10, 'color': 'dimgray', 'weight': 'light'}
    
    ## Use gridspec to set up a plot with a series of subplots that is
    ## n-rows by n-columns
    gs = GridSpec(nrows, ncols, height_ratios=[1, 0.05, 0.05], width_ratios = [1], wspace=0.05, hspace=0.1)
    ## use gs[rows index, columns index] to access grids
    
    ax = fig.add_subplot(gs[0, 0], projection=mapcrs)
        
    ax = draw_basemap(ax, extent=ext, xticks=dx, yticks=dy, left_lats=True, right_lats=False, bottom_lons=True)
    
    ## set cmap and contour values based on varname
    if varname == 'ivt':
        cmap_name = 'mclimate_red'
        clevs = np.arange(250., 2100., 250.)
    elif varname == 'freezing_level':
        cmap_name = 'mclimate_green'
        clevs = np.arange(0., 60000., 1500.)
        fc[varname] = fc[varname]*3.281 # convert to feet
    elif varname == 'uv1000':
        cmap_name = 'mclimate_purple'
        clevs = np.arange(0., 55., 5.)
    
    # Contour Filled (mclimate values)
    data = ds.sel(step=step).mclimate.values*100.
    cmap, norm, bnds, cbarticks, cbarlbl = ccmap.cmap(cmap_name)
    cf = ax.contourf(lons, lats, data, transform=datacrs,
                     levels=bnds, cmap=cmap, norm=norm, alpha=0.9, extend='neither')
    
    # Contour Lines (forecast values)
    forecast = fc.sel(step=step)     
    cs = ax.contour(lons, lats, forecast[varname], transform=datacrs,
                     levels=clevs, colors='k',
                     linewidths=0.75, linestyles='solid')
    plt.clabel(cs, **kw_clabels)
    
    # Add color bar
    cbax = plt.subplot(gs[1,0]) # colorbar axis
    cbarticks = list(itertools.compress(bnds, cbarticks)) ## this labels the cbarticks based on the cmap dictionary
    cb = Colorbar(ax = cbax, mappable = cf, orientation = 'horizontal', 
                  ticklocation = 'bottom', ticks=cbarticks)
    cb.set_label(cbarlbl, fontsize=11)
    cb.ax.tick_params(labelsize=12)
    
    init_time = ts.strftime('%HZ %d %b %Y')
    start_date = ts - timedelta(days=45)
    start_date = start_date.strftime('%d-%b')
    end_date = ts + timedelta(days=45)
    end_date = end_date.strftime('%d-%b')
    
    ts_valid = ts + timedelta(hours=int(step))
    valid_time = ts_valid.strftime('%HZ %d %b %Y')
    
    ax.set_title('Initialized: {0}'.format(init_time), loc='left', fontsize=10)
    ax.set_title('F-{0} | Valid: {1}'.format(int(step), valid_time), loc='right', fontsize=10)

    
    txt = 'Relative to all {2}-h GEFSv12 reforecasts initialized between {0} and {1} (2000-2019)'.format(start_date, end_date, step)
    ann_ax = fig.add_subplot(gs[-1, 0])
    ann_ax.axis('off')
    ann_ax.annotate(textwrap.fill(txt, 101), # this is the text
               (0, 0.3), # these are the coordinates to position the label
                textcoords="offset points", # how to position the text
                xytext=(0,-19), # distance from text to points (x,y)
                ha='left', # horizontal alignment can be left, right or center
                **kw_ticklabels)
    
    fig.savefig('%s.%s' %(fname, fmt), bbox_inches='tight', dpi=fig.dpi)

    plt.close(fig)

def plot_mclimate_forecast_comparison(ds_lst, fc_lst, varname, fname, ext=[-170., -120., 40., 65.]):
    # Set up projection
    mapcrs = ccrs.Mercator()
    # mapcrs = ccrs.PlateCarree()
    datacrs = ccrs.PlateCarree()
    
    # Set tick/grid locations
    lats = fc_lst[0].lat.values
    lons = fc_lst[0].lon.values
    dx = np.arange(lons.min().round(),lons.max().round()+10,10)
    dy = np.arange(lats.min().round(),lats.max().round()+5,5)
    
    # Create figure
    fig = plt.figure(figsize=(13, 5))
    fig.dpi = 300
    fmt = 'png'
    
    nrows = 1
    ncols = 3
    
    # contour labels
    kw_clabels = {'fontsize': 7, 'inline': True, 'inline_spacing': 7, 'fmt': '%i',
                  'rightside_up': True, 'use_clabeltext': True}
    
    kw_ticklabels = {'size': 10, 'color': 'dimgray', 'weight': 'light'}
    
    ## Use gridspec to set up a plot with a series of subplots that is
    ## n-rows by n-columns
    gs = GridSpec(nrows, ncols, height_ratios=[1], width_ratios = [1, 1, 0.05], wspace=0.001, hspace=0.05)
    ## use gs[rows index, columns index] to access grids
    
    ###################
    ### PLOT FIGURE ###
    ###################
    leftlats_lst = [True, False]
    for i, (fc, ds) in enumerate(zip(fc_lst, ds_lst)):
        ax = fig.add_subplot(gs[0, i], projection=mapcrs) 
        ax = draw_basemap(ax, extent=ext, xticks=dx, yticks=dy, left_lats=leftlats_lst[i], right_lats=False, bottom_lons=True)
        
        ## set cmap and contour values based on varname
        if varname == 'ivt':
            cmap_name = 'mclimate_red'
            clevs = np.arange(250., 2100., 250.)
        elif varname == 'freezing_level':
            cmap_name = 'mclimate_green'
            clevs = np.arange(0., 60000., 1500.)
            fc[varname] = fc[varname]*3.281 # convert to feet
        elif varname == 'uv1000':
            cmap_name = 'mclimate_purple'
            clevs = np.arange(0., 55., 5.)
        
        # Contour Filled
        data = ds.mclimate.values*100.    
        cmap, norm, bnds, cbarticks, cbarlbl = ccmap.cmap(cmap_name)
        cf = ax.contourf(ds.lon, ds.lat, data, transform=datacrs,
                         levels=bnds, cmap=cmap, norm=norm, alpha=0.9, extend='neither')
        
        # Contour Lines
        cs = ax.contour(fc.lon, fc.lat, fc[varname], transform=datacrs,
                         levels=clevs, colors='k',
                         linewidths=0.75, linestyles='solid')
        plt.clabel(cs, **kw_clabels)
        
        ts = pd.to_datetime(str(fc.init_date.values)) 
        init_time = ts.strftime('%HZ %d %b %Y')
        start_date = ts - timedelta(days=45)
        start_date = start_date.strftime('%d-%b')
        end_date = ts + timedelta(days=45)
        end_date = end_date.strftime('%d-%b')
        
        ts = pd.to_datetime(str(fc.valid_time.values)) 
        valid_time = ts.strftime('%HZ %d %b %Y')
        
        ax.set_title('Model Run: {0}'.format(init_time), loc='left', fontsize=10)
        ax.set_title('Valid Date: {0}'.format(valid_time), loc='right', fontsize=10)
    
        
        txt = 'Relative to all {2}-h GEFSv12 reforecasts initialized between {0} and {1} (2000-2019)'.format(start_date, end_date, fc.step.values)
        ann_ax = fig.add_subplot(gs[-1, i])
        ann_ax.axis('off')
        ann_ax.annotate(textwrap.fill(txt, 60), # this is the text
                   (0, 0.), # these are the coordinates to position the label
                    textcoords="offset points", # how to position the text
                    xytext=(25,-35), # distance from text to points (x,y)
                    ha='left', # horizontal alignment can be left, right or center
                    **kw_ticklabels)
    
    # Add color bar
    cbax = plt.subplot(gs[0,-1]) # colorbar axis
    cbarticks = list(itertools.compress(bnds, cbarticks)) ## this labels the cbarticks based on the cmap dictionary
    cb = Colorbar(ax = cbax, mappable = cf, orientation = 'vertical', 
                  ticklocation = 'right', ticks=cbarticks)
    cb.set_label(cbarlbl, fontsize=10)
    cb.ax.tick_params(labelsize=8)
    
    fig.savefig('%s.%s' %(fname, fmt), bbox_inches='tight', dpi=fig.dpi)
    
    # Show
    plt.show()

def add_subregion_boxes(ax, subregion_xy, width, height, ecolor, datacrs):
    '''This function will add subregion boxes to the given axes.
    subregion_xy 
    [[ymin, xmin], [ymin, xmin]]
    '''
    for i in range(len(subregion_xy)):
        ax.add_patch(mpatches.Rectangle(xy=subregion_xy[i], width=width[i], height=height[i],
                                        fill=False,
                                        edgecolor=ecolor,
                                        linewidth=1.0,
                                        transform=datacrs,
                                        zorder=100))
        
    return ax

        
def plot_maxmin_points(lon, lat, data, extrema, nsize, symbol, color='k',
                       plotValue=True, transform=None):
    """
    This function will find and plot relative maximum and minimum for a 2D grid. The function
    can be used to plot an H for maximum values (e.g., High pressure) and an L for minimum
    values (e.g., low pressue). It is best to used filetered data to obtain  a synoptic scale
    max/min value. The symbol text can be set to a string value and optionally the color of the
    symbol and any plotted value can be set with the parameter color
    lon = plotting longitude values (2D)
    lat = plotting latitude values (2D)
    data = 2D data that you wish to plot the max/min symbol placement
    extrema = Either a value of max for Maximum Values or min for Minimum Values
    nsize = Size of the grid box to filter the max and min values to plot a reasonable number
    symbol = String to be placed at location of max/min value
    color = String matplotlib colorname to plot the symbol (and numerica value, if plotted)
    plot_value = Boolean (True/False) of whether to plot the numeric value of max/min point
    The max/min symbol will be plotted on the current axes within the bounding frame
    (e.g., clip_on=True) 
    
    ^^^ Notes from MetPy. Function adapted from MetPy.
    """
    from scipy.ndimage.filters import maximum_filter, minimum_filter

    if (extrema == 'max'):
        data_ext = maximum_filter(data, nsize, mode='nearest')
    elif (extrema == 'min'):
        data_ext = minimum_filter(data, nsize, mode='nearest')
    else:
        raise ValueError('Value for hilo must be either max or min')

    mxy, mxx = np.where(data_ext == data)

    for i in range(len(mxy)):
        ax.text(lon[mxy[i], mxx[i]], lat[mxy[i], mxx[i]], symbol, color=color, size=13,
                clip_on=True, horizontalalignment='center', verticalalignment='center',
                fontweight='extra bold',
                transform=transform)
        ax.text(lon[mxy[i], mxx[i]], lat[mxy[i], mxx[i]],
                '\n \n' + str(np.int(data[mxy[i], mxx[i]])),
                color=color, size=8, clip_on=True, fontweight='bold',
                horizontalalignment='center', verticalalignment='center', 
                transform=transform, zorder=10)
        
    return ax

def loadCPT(path):
    """A function that loads a .cpt file and converts it into a colormap for the colorbar.
    
    This code was adapted from the GEONETClass Tutorial written by Diego Souza, retrieved 18 July 2019. 
    https://geonetcast.wordpress.com/2017/06/02/geonetclass-manipulating-goes-16-data-with-python-part-v/
    
    Parameters
    ----------
    path : 
        Path to the .cpt file
        
    Returns
    -------
    cpt :
        A colormap that can be used for the cmap argument in matplotlib type plot.
    """
    
    try:
        f = open(path)
    except:
        print ("File ", path, "not found")
        return None
 
    lines = f.readlines()
 
    f.close()
 
    x = np.array([])
    r = np.array([])
    g = np.array([])
    b = np.array([])
 
    colorModel = 'RGB'
 
    for l in lines:
        ls = l.split()
        if l[0] == '#':
            if ls[-1] == 'HSV':
                colorModel = 'HSV'
                continue
            else:
                continue
        if ls[0] == 'B' or ls[0] == 'F' or ls[0] == 'N':
            pass
        else:
            x=np.append(x,float(ls[0]))
            r=np.append(r,float(ls[1]))
            g=np.append(g,float(ls[2]))
            b=np.append(b,float(ls[3]))
            xtemp = float(ls[4])
            rtemp = float(ls[5])
            gtemp = float(ls[6])
            btemp = float(ls[7])
 
        x=np.append(x,xtemp)
        r=np.append(r,rtemp)
        g=np.append(g,gtemp)
        b=np.append(b,btemp)
 
    if colorModel == 'HSV':
        for i in range(r.shape[0]):
            rr, gg, bb = colorsys.hsv_to_rgb(r[i]/360.,g[i],b[i])
        r[i] = rr ; g[i] = gg ; b[i] = bb
 
    if colorModel == 'RGB':
        r = r/255.0
        g = g/255.0
        b = b/255.0
 
    xNorm = (x - x[0])/(x[-1] - x[0])
 
    red   = []
    blue  = []
    green = []
 
    for i in range(len(x)):
        red.append([xNorm[i],r[i],r[i]])
        green.append([xNorm[i],g[i],g[i]])
        blue.append([xNorm[i],b[i],b[i]])
 
    colorDict = {'red': red, 'green': green, 'blue': blue}
    # Makes a linear interpolation
    cpt = LinearSegmentedColormap('cpt', colorDict)
    
    return cpt


def make_cmap(colors, position=None, bit=False):
    '''
    make_cmap takes a list of tuples which contain RGB values. The RGB
    values may either be in 8-bit [0 to 255] (in which bit must be set to
    True when called) or arithmetic [0 to 1] (default). make_cmap returns
    a cmap with equally spaced colors.
    Arrange your tuples so that the first color is the lowest value for the
    colorbar and the last is the highest.
    position contains values from 0 to 1 to dictate the location of each color.
    '''
    import matplotlib as mpl
    import numpy as np
    bit_rgb = np.linspace(0,1,256)
    if position == None:
        position = np.linspace(0,1,len(colors))
    else:
        if len(position) != len(colors):
            sys.exit("position length must be the same as colors")
        elif position[0] != 0 or position[-1] != 1:
            sys.exit("position must start with 0 and end with 1")
    if bit:
        for i in range(len(colors)):
            colors[i] = (bit_rgb[colors[i][0]],
                         bit_rgb[colors[i][1]],
                         bit_rgb[colors[i][2]])
    cdict = {'red':[], 'green':[], 'blue':[]}
    for pos, color in zip(position, colors):
        cdict['red'].append((pos, color[0], color[0]))
        cdict['green'].append((pos, color[1], color[1]))
        cdict['blue'].append((pos, color[2], color[2]))

    cmap = mpl.colors.LinearSegmentedColormap('my_colormap',cdict,256)
    return cmap

def nice_intervals(data, nlevs):
    '''
    Purpose::
        Calculates nice intervals between each color level for colorbars
        and contour plots. The target minimum and maximum color levels are
        calculated by taking the minimum and maximum of the distribution
        after cutting off the tails to remove outliers.
    Input::
        data - an array of data to be plotted
        nlevs - an int giving the target number of intervals
    Output::
        clevs - A list of floats for the resultant colorbar levels
    '''
    # Find the min and max levels by cutting off the tails of the distribution
    # This mitigates the influence of outliers
    data = data.ravel()
    mn = mstats.scoreatpercentile(data, 5)
    mx = mstats.scoreatpercentile(data, 95)
    # if min less than 0 and or max more than 0 put 0 in center of color bar
    if mn < 0 and mx > 0:
        level = max(abs(mn), abs(mx))
        mnlvl = -1 * level
        mxlvl = level
    # if min is larger than 0 then have color bar between min and max
    else:
        mnlvl = mn
        mxlvl = mx

    # hack to make generated intervals from mpl the same for all versions
    autolimit_mode = mpl.rcParams.get('axes.autolimit_mode')
    if autolimit_mode:
        mpl.rc('axes', autolimit_mode='round_numbers')

    locator = mpl.ticker.MaxNLocator(nlevs)
    clevs = locator.tick_values(mnlvl, mxlvl)
    if autolimit_mode:
        mpl.rc('axes', autolimit_mode=autolimit_mode)

    # Make sure the bounds of clevs are reasonable since sometimes
    # MaxNLocator gives values outside the domain of the input data
    clevs = clevs[(clevs >= mnlvl) & (clevs <= mxlvl)]
    return clevs


def _drawmap(fig, lons, lats, VO1, VO2, VO3, cmap1, cmap2, cmap3, clevs1, clevs2, clevs3, title, ext,
             datacrs, mapcrs, ndeg=10.):
    '''Draw contour map for create_animation.'''
    # Clear current axis to overplot next time step
    ax = fig.gca()
    ax.clear()
    # Add subplot, title, and set extent
    ax = fig.add_subplot(1,1,1, projection=mapcrs)
    xticks = np.arange(ext[0], ext[1]+ndeg, ndeg)
    yticks = np.arange(ext[2], ext[3]+ndeg, ndeg)
    
#     ax = draw_basemap(ax, datacrs=datacrs, 
#                  extent=ext, xticks=None, yticks=None, 
#                  grid=False, left_lats=True, right_lats=False, 
#                  bottom_lons=True, mask_ocean=False)
    
    ax.set_extent(ext, crs=mapcrs)
    
    # Add Border Features
    coast = ax.coastlines(linewidths=1.0)
    ax.add_feature(cfeature.BORDERS)
    
    # Add grid lines
    gl = ax.gridlines(crs=datacrs, draw_labels=True,
                      linewidth=.5, color='black', alpha=0.5, linestyle='--')
    gl.top_labels = False
    gl.left_labels = True
    gl.right_labels = False
    gl.bottom_labels = True
    gl.xlocator = mticker.FixedLocator(xticks)
    gl.ylocator = mticker.FixedLocator(yticks)
    gl.xformatter = LONGITUDE_FORMATTER
    gl.yformatter = LATITUDE_FORMATTER
    gl.xlabel_style = {'size': 10, 'color': 'gray'}
    gl.ylabel_style = {'size': 10, 'color': 'gray'}
    
    # Add contour plot (line)
    cs = ax.contour(lons, lats, VO2, transform=datacrs,
                    levels=clevs2, colors='grey', linewidths=0.7, linestyles='solid', zorder=10)
    kw_clabels = {'fontsize': 8, 'inline': True, 'inline_spacing': 10, 'fmt': '%i',
                  'rightside_up': True, 'use_clabeltext': True}
    plt.clabel(cs, **kw_clabels)
    
    # Add contour plot (shaded precip)
    cf2 = ax.contourf(lons, lats, VO3, transform=datacrs, cmap=cmap3, levels=clevs3, zorder=5, extend='max', alpha=0.5)
    
    # Add contour plot (shaded)
    cf = ax.contourf(lons, lats, VO1, transform=datacrs, cmap=cmap1, levels=clevs1, zorder=0, extend='max', alpha=0.8)
    
    ax.set_title(title, fontsize=14)
    
    # Add a color bar
    cbar = fig.colorbar(cf, orientation='vertical', cmap=cmap1, shrink=0.99)
#     cbar.set_label(units, fontsize=12)
    
#     # add second colorbar
#     rect_loc = [1.02, 0.08, 0.03, 0.87]  # define position 
#     cax2 = fig.add_axes(rect_loc)       # left | bottom | width | height
#     cbar2  = plt.colorbar(second_contour, cax=cax2)
    
    return cf, cf2, ax

def _myanimate(i, fig, DS, var1, var2, var3, lats, lons, cmap1, cmap2, cmap3, clevs1, clevs2, clevs3, ext, datacrs, mapcrs):
    '''Loop through time steps for create_animation.'''
    # Clear current axis to overplot next time step
    ax = fig.gca()
    ax.clear()
    # Loop through time steps in ds
    VO1 = DS[var1].values[i]
    VO2 = DS[var2].values[i]
    VO3 = DS[var3].values[i]
    # Set title based on long name and current time step
    ts = pd.to_datetime(str(DS.time.values[i])).strftime("%Y-%m-%d %H:%M")
    long_name = DS[var1].long_name
    title = '{0} at {1}'.format(long_name, ts)
    # Add next contour map
    new_contour, new_contour2, new_ax = _drawmap(fig, lons, lats, VO1, VO2, VO3, cmap1, cmap2, cmap3, clevs1, clevs2, clevs3, title, ext, datacrs, mapcrs) 
    
    return new_ax

def create_animation(DS, var1, var2, var3, clevs1, clevs2, clevs3, cmap1, cmap2, cmap3, 
                     ext=[-180.0, 180.0, -90., 90.], datacrs=ccrs.PlateCarree(), mapcrs=ccrs.PlateCarree()):
    '''Create an mp4 animation using an xarray dataset with lat, lon, and time dimensions.
    
        Parameters
        ----------
        DS: xarray dataset object
        
        var: string
            Variable name to plot
        clevs: int
            Contour levels to plot
        cmap: string
            Colormap for plotting
            
        Returns
        -------
        filename, mp4 file of animation
        
        '''
    
    # Get information from ds
    lats = DS.lat
    lons = DS.lon
    long_name = DS[var1].long_name
    units = DS[var1].units
    t0 = pd.to_datetime(str(DS.time.values[0])).strftime("%Y-%m-%d %H:%M")
    title = '{0} at {1}'.format(long_name, t0)
    FFMpegWriter = animation.writers['ffmpeg']
    metadata = dict(title=title,
                    comment='')
    writer = FFMpegWriter(fps=20, metadata=metadata)
    
    # Create a new figure window
    fig = plt.figure(figsize=[8,4])
#     # Draw first timestep
    first_contour, second_contour, first_ax = _drawmap(fig, lons, lats, DS[var1].values[0], DS[var2].values[0], DS[var3].values[0], cmap1, cmap2, cmap3, clevs1, clevs2, clevs3, title, ext, datacrs, mapcrs)

    # Loop through animation
    ani = animation.FuncAnimation(fig, _myanimate, frames=np.arange(len(DS[var1])),
                                  fargs=(fig, DS, var1, var2, var3, lats, lons, cmap1, 
                                         cmap2, cmap3, clevs1, clevs2, clevs3, ext, datacrs, mapcrs), interval=50)
    filename = long_name + ".mp4"
    ani.save(long_name + ".mp4")
    
    # save animation at 30 frames per second 
    ani.save(long_name + ".gif", writer='imagemagick', fps=10)
    
    return filename

def get_every_other_vector(x):
    '''
    stagger matrix setting values to diagonal
    based on https://www.w3resource.com/python-exercises/numpy/basic/numpy-basic-exercise-30.php

    Parameters
    ----------
    x : 2-D array

    Returns
    -------
    x : 2-D array
    same array as input but with the values staggered
    [[ 1.  0.  1.  0.]
     [ 0.  1.  0.  1.]
     [ 1.  0.  1.  0.]
     [ 0.  1.  0.  1.]]
    '''
    x[::2, 1::2] = 0
    x[1::2, ::2] = 0

    return x