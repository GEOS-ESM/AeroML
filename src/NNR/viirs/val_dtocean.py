#!/usr/bin/env python3
"""
    Validate the Dark Target Ocean Obs
    Make publication ready plots
"""

import os, sys
from   pyabc.abc_viirs            import ABC_DT_Ocean
from   glob                       import glob
import argparse
import numpy as np
import matplotlib.pyplot    as      plt
from scipy import stats
from matplotlib import ticker
#------
class aodFormat(ticker.Formatter):
    def __call__(self,x,pos=None):
        y = np.exp(x)-0.01
        return '%4.2f'%y

def _cat2 (X, Y):
    """
    Given 2 arrays of same shape, returns array of shape (2,N),
    where N = X.size = Y.size
    """
    xy = np.concatenate((X.ravel(),Y.ravel())) # shape is (N+N)
    return np.reshape(xy,(2,X.size))         # shape is (2,N)


def _plot2dKDE(x_values,y_values,x_bins=None,y_bins=None,
             x_label='AERONET', y_label='STANDARD',figfile=None,title=None):
    """
    Plot Target vs Model using a 2D Kernel Density Estimate.
    """

    if x_bins is None: x_bins = np.arange(-5., 1., 0.1 )
    if y_bins is None: y_bins = x_bins

    Nx = len(x_bins)
    Ny = len(y_bins)

    print("Evaluating 2D kernel on grid with (Nx,Ny)=(%d,%d) ..."%(Nx,Ny))
    kernel = stats.gaussian_kde(_cat2(x_values,y_values))
    X, Y = np.meshgrid(x_bins,y_bins)   # each has shape (Ny,Nx)
    Z = kernel(_cat2(X,Y))           # shape is (Ny*Nx)
    Z = np.reshape(Z,X.shape)

    # --- Calculate Statistics ---
    N = len(x_values)
    diff = np.array(y_values) - np.array(x_values)
    bias = np.mean(diff)
    # Calculate R-squared using Pearson correlation coefficient
    r_val = np.corrcoef(x_values, y_values)[0, 1]
    r2 = r_val**2

    # Calculate RMSE
    rmse = np.sqrt(np.mean(diff**2))

    # Create the text string for the legend box
    stat_str = f"N = {N}\n$R^2$ = {r2:.3f}\nBias = {bias:.3f}\nRMSE = {rmse:.3f}"


    formatter = aodFormat()

    fig = plt.figure()
    ax = fig.add_axes([0.1,0.1,0.75,0.75])
    ax.xaxis.set_major_formatter(formatter)
    ax.yaxis.set_major_formatter(formatter)
    ax.imshow(Z, cmap=plt.cm.gist_earth_r, origin='lower',
           extent=(x_bins[0],x_bins[-1],y_bins[0],y_bins[-1]) )
    ax.plot([x_bins[0],x_bins[-1]],[y_bins[0],y_bins[-1]],'k')
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.grid()
    if title is not None:
        ax.set_title(title)

    # --- Add Statistics Box ---
    # Place text in the upper left corner of the axes
    props = dict(boxstyle="square",facecolor='white', alpha=0.8, edgecolor='gray')
#    ax.text(0.05, 0.95, stat_str, transform=ax.transAxes, fontsize=10,
#            verticalalignment='top', horizontalalignment='left', bbox=props)

    # Place text in the upper right corner of the axes
    ax.text(0.70, 0.97, stat_str, transform=ax.transAxes, fontsize=10,
            verticalalignment='top', horizontalalignment='left', bbox=props)    


    # --- Add Scatter Inset Plot ---
    # Top-Right corner: [left, bottom, width, height]
#    ax_scatter = ax.inset_axes([0.65, 0.70, 0.30, 0.25])

    # Top-Left corner: [left, bottom, width, height]
    ax_scatter = ax.inset_axes([0.15, 0.70, 0.30, 0.25])

    ax_scatter.scatter(x_values, y_values, c='k', s=1, alpha=0.3)
    ax_scatter.plot([x_bins[0], x_bins[-1]], [y_bins[0], y_bins[-1]], 'r--', linewidth=1) # 1:1 line
    
    # Match axes bounds to the main plot
    ax_scatter.set_xlim(x_bins[0], x_bins[-1])
    ax_scatter.set_ylim(y_bins[0], y_bins[-1])
    ax_scatter.set_title("Scatter", fontsize=8, pad=3)
    ax_scatter.tick_params(axis='both', labelsize=6)
    ax_scatter.set_facecolor((1, 1, 1, 0.8)) # Semi-transparent white background
    ax_scatter.set_xlabel(x_label,fontsize=8)
    ax_scatter.set_ylabel(y_label,fontsize=8)
    ax_scatter.grid()
    ax_scatter.xaxis.set_major_formatter(formatter)
    ax_scatter.yaxis.set_major_formatter(formatter)

    # --- Add 1D KDE Inset Plot (Difference) ---
    # Bottom-Right corner. Coordinates: [left, bottom, width, height] (fractions of main axes)
    ax_inset = ax.inset_axes([0.6, 0.05, 0.35, 0.25])
    
    print("Evaluating 1D kernel for differences...")
    diff = y_values - x_values
    kde_1d = stats.gaussian_kde(diff)
    
    # Create an evaluation grid based on the min/max of the difference
#    lim = np.max(np.abs(diff))
    lim = 1.5
    diff_grid = np.linspace(-1*lim, lim, 200)
    pdf_1d = kde_1d(diff_grid)
    
    ax_inset.plot(diff_grid, pdf_1d, color='black', linewidth=1.5)
    ax_inset.fill_between(diff_grid, pdf_1d, color='gray', alpha=0.4)
    ax_inset.axvline(0, color='red', linestyle='--', linewidth=1) # Zero bias reference line
    
    # Formatting the inset
    ax_inset.set_title(f'{y_label} - {x_label}\n[log(AOD+0.01)]', fontsize=8, pad=3)
    ax_inset.set_yticks([]) # Hide Y-axis labels/ticks on the density plot
    ax_inset.tick_params(axis='x', labelsize=8)
    
    # Optional: Match inset facecolor/transparency so it stands out from the main plot
    ax_inset.set_facecolor((1, 1, 1, 0.8)) 



    if figfile is not None:
        plt.savefig(figfile)
        plt.close(fig)
    else:
        plt.show()




if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("inputs",
                        help="python file with dictionary of inputs")
    parser.add_argument("--test",action='store_true',
                        help="this is a testing dataset")


    args = parser.parse_args()

    # read in dictionary of input parameters
    s = open(args.inputs).read()
    inputs = eval(s)

    # --------------
    # Setup Inputs
    # -------------

    # giantFile
    giantFile = []
    for gFile in inputs['giantFile']:
        giantFile += sorted(glob(gFile))

    aerFile = []
    for aFile in inputs['aerFile']:
        aerFile += sorted(glob(aFile))

    # tymemax sets a truncation date when reading in giant file
    # string with format YYYYMMDD
    # None reads the entire datarecord
    tymemax = inputs['tymemax']

    # how many std dev to use for outlier removal. If < 0, don't do outlier removal
    # default is 3
    outliers = inputs['outliers']

    # number of hidden layers
    nHLayers     = inputs['nHLayers']
    
    # number of nodes in hidden layers
    # None uses the default of 200 coded in nn.py        
    nHidden      = inputs['nHidden']

    # do training on combinations of the inputs
    combinations = inputs['combinations']

    # NN target variable name
    Target       = inputs['Target']

    # surface albedo variable name
    # options are None, CoxMunkLUT, or CxAlbedo
    # if CoxMunkLUT one needs to provide the coxmunk_lut option to ABC_Ocean, 
    # otherwise default is used (default = '/nobackup/NNR/Misc/coxmunk_lut.npz')
    # if CxAlbedo is used, need to provide a *npz file with CxAlbedo precalculated
    Albedo       = inputs['Albedo']

    # number of K-folds or training
    # if None does not do K-folding, trains on entire dataset
    K            = inputs['K']

    # Flags to Train or Test the DARK TARGET DATASET
    # Always false when doing valiation
    doTrain      = False
    doTest       = False

    # experiment name
    expid        = inputs['expid']

    # Inputs that are always included
    # this can be None
    Input_const = inputs['Input_const']


    # Inputs that can be varied across combinations
    # if combinations flag is False, all of these inputs are used
    # if combinations flag is True, all possible combinations of these inputs
    # are tried
    Input_nnr = inputs['Input_nnr']

    # Inputs I want to the the log-transform of
    lInput_nnr = inputs['lInput_nnr']

    # Additional variables that the inputs are filtered by
    # standard filters are hardcoded in the abc_c6.py scripts 
    aFilter  = inputs['aFilter']

    # fraction that defines whether a pixel is domniated by a species
    f_balance = inputs['f_balance']

    # flag to do both species and target AOD balancing
    q_balance = inputs['q_balance']
    q_balance_enhance = inputs['q_balance_enhance']

    # minimum number of points to have in a size bin for balancing
    # this is an adhoc parameter, but if it's too small, no obs will make
    # it through balancing procedure
    minN = inputs['minN']

    # ignore a species when doing species balancing step
    # is spc_aod_balance
    # ignore SS dominated over land because these obs are so few
    fignore = inputs['fignore']

    # number of size bins to use in aod balancing
    # default is 6
    nbins = inputs['nbins']

    # cloud threshhold for filtering
    # default if not provided is 0.7
    cloud_thresh = inputs['cloud_thresh']

    # take natural log of target aod
    # detault is true
    laod = inputs['laod']

    # offset to protect against negative numbers.
    # detault is 0.01
    logoffset = inputs['logoffset']

    # standard scale the targets
    scale = inputs['scale']

    # oversample values less than epsilon value
    near_zero_weight_epsilon = inputs['near_zero_weight_epsilon']

    # oversample inputs values greater than percentile
    # default is None, don't do weighting
    exp_weight_percentile = inputs['exp_weight_percentile']

    # training iterations
    # default if not provided is 2250
    maxfun = inputs['maxfun']

    # --------------
    # End of Inputs
    # -------------

    # get satellite name from giantFile name
    if type(giantFile) is str:
        sat = giantFile.split('_')[-4]
    else:
        sat = giantFile[0].split('_')[-4]

    if sat == 'SNPP':
        retrieval    = 'VS_DT_OCEAN'
    if sat in ['NOAA20','NOAA-20']:
        retrieval    = 'VN20_DT_OCEAN'

    expid        = '{}_{}'.format(retrieval,expid)

    if Input_const is not None:
        InputMaster = list((Input_const,) + tuple(Input_nnr))
    else:
        InputMaster = Input_nnr

    # Read in the Giant File
    # and set up datasets
    # -------------------------------------
    ocean = ABC_DT_Ocean(giantFile,aerFile=aerFile,Albedo=Albedo,
                verbose=1,aFilter=aFilter,tymemax=tymemax,cloud_thresh=cloud_thresh,outliers=outliers,
                logoffset=logoffset,laod=laod,scale=scale,near_zero_weight_epsilon=near_zero_weight_epsilon)



    # Initialize class for training/testing
    # ---------------------------------------------
    ocean.setupNN(retrieval, expid,
                      nHidden      = nHidden,
                      nHLayers     = nHLayers,
                      combinations = combinations,
                      Input_const  = Input_const,
                      Input_nnr    = Input_nnr,                                         
                      Target       = Target,                      
                      K            = K,
                      lInput_nnr   = lInput_nnr,
                      f_balance    = f_balance,
                      q_balance    = q_balance,
                      q_balance_enhance = q_balance_enhance,
                      minN         = minN,
                      fignore      = fignore,
                      nbins        = nbins)


    # create directory for saving plots
    # -----------------------------------
    if args.test:
        outdir = 'test_dtocean_plots'
    else:
        outdir = 'val_dtocean_plots'
    os.makedirs(outdir,exist_ok=True)

    invars = ocean.comblist[0]
    netFile = ocean.outdir+"/"+".".join(invars)+'_Tau.net'

    
    # load the net
    ocean.net = ocean.loadnet(netFile)
    ocean.Input = ocean.comblist[0]

    # set I
    I = ocean.iTest

    # Get the target, original data, and NN predicted data
    targets  = ocean.getTargets(I,noscale=True)
    results = ocean.eval(I,noscale=True).squeeze()
    name = 'm'+ocean.Target[0][1:]
    original = np.log(ocean.__dict__[name][I] + 0.01)

    figfile = outdir + '/kde2d_dtocean_std.png'
    _plot2dKDE(targets,original,x_bins=None,y_bins=None,
             x_label='AERONET', y_label='STANDARD Retrieval',figfile=figfile,title='DT-OCEAN 550 nm AOD') 

    figfile = outdir + '/kde2d_dtocean_nnr.png'
    _plot2dKDE(targets,results,x_bins=None,y_bins=None,
             x_label='AERONET', y_label='NNR Retrieval',figfile=figfile,title='DT-OCEAN 550 nm AOD')


    # if outlier were excluded, do an extra test with outliers included
    if (outliers > 0):
        ocean_out = ABC_DT_Ocean(giantFile,aerFile=aerFile,Albedo=Albedo,
                verbose=1,aFilter=aFilter,tymemax=tymemax,cloud_thresh=cloud_thresh,outliers=-1,
                logoffset=logoffset,laod=laod,scale=scale)        

        ocean_out.setupNN(retrieval, expid,
                  nHidden      = nHidden,
                  nHLayers     = nHLayers,
                  combinations = combinations,
                  Input_const  = Input_const,
                  Input_nnr    = Input_nnr,
                  Target       = Target,
                  K            = K,
                  lInput_nnr   = lInput_nnr,
                  f_balance    = 0,
                  q_balance    = False,
                  minN         = minN,
                  fignore      = fignore,
                  nbins        = nbins)           

        ocean_out.iTest[ocean.outValid][ocean.iTrain] = False


        # load the net
        ocean_out.net = ocean.net
        ocean_out.Input = ocean.Input

        # set I
        I = ocean_out.iTest

        # Get the target, original data, and NN predicted data
        targets  = ocean_out.getTargets(I,noscale=True)
        results = ocean_out.eval(I,noscale=True).squeeze()
        name = 'm'+ocean_out.Target[0][1:]
        original = np.log(ocean_out.__dict__[name][I] + 0.01)

        figfile = outdir + '/kde2d_dtocean_outliers_std.png'
        _plot2dKDE(targets,original,x_bins=None,y_bins=None,
             x_label='AERONET', y_label='STANDARD Retrieval',figfile=figfile,title='DT-OCEAN 550 nm AOD')

        figfile = outdir + '/kde2d_dtocean_outliers_nnr.png'
        _plot2dKDE(targets,results,x_bins=None,y_bins=None,
             x_label='AERONET', y_label='NNR Retrieval',figfile=figfile,title='DT-OCEAN 550 nm AOD')


