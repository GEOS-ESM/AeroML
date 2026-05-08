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


#------
def _plot2dKDE(self,x_values,y_values,x_bins=None,y_bins=None,
             x_label='AERONET', y_label='STANDARD',figfile=None,title=None):
    """
    Plot Target vs Model using a 2D Kernel Density Estimate.
    """

    if x_bins is None: x_bins = np.arange(-5., 1., 0.1 )
    if y_bins is None: y_bins = x_bins

    Nx = len(x_bins)
    Ny = len(y_bins)

    print("Evaluating 2D kernel on grid with (Nx,Ny)=(%d,%d) ..."%(Nx,Ny))
    kernel = stats.kde.gaussian_kde(self._cat2(x_values,y_values))
    X, Y = np.meshgrid(x_bins,y_bins)   # each has shape (Ny,Nx)
    Z = kernel(_cat2(X,Y))           # shape is (Ny*Nx)
    Z = np.reshape(Z,X.shape)

    if self.laod:
        formatter = aodFormat()
    else:
        formatter = None

    fig = plt.figure()
    ax = fig.add_axes([0.1,0.1,0.75,0.75])
    if formatter != None:
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

    if figfile is not None:
        plt.savefig(figfile)
        plt.close(fig)
    else:
        plt.show()




if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("inputs",
                        help="python file with dictionary of inputs")
    parser.add_argument("--oldnet",action='store_true',
                        help="continue training from an existing netfile")    

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


    invars = ocean.comblist[0]
    netFile = ocean.outdir+"/"+".".join(invars)+'_Tau.net'

    
    # load the net
    ocean.net = ocean.loadnet(netFile)
    ocean.Input = ocean.comblist[0]

    # set I
    I = ocean.iTest

    # Get the target, original data, and NN predicted data
    targets  = ocean.getTargets(I,noscale=True)
    targets.shape = targets.shape + (1,)
    results = ocean.eval(I,noscale=True)
    name = 'm'+ocean.Target[0][1:]
    original = np.log(ocean.__dict__[name][I] + 0.01)

     

    sys.exit()


    # Do Training and Testing
    # ------------------------
    if doTrain:
        lossFile = f"{ocean.outdir}/training_loss.pkl"
        kwargs = {'maxfun':maxfun,
                  'messages': 9,
                 }
#                  'bounds': [None,None]}
        if args.oldnet:
            newnet= False
            with open(lossFile, "rb") as f:
                loss = pickle.load(f)
                ocean.ermse = loss['ermse']
                ocean.emae  = loss['emae']
                ocean.eme   = loss['eme']
                ocean.esqerr = loss['esqerr']
        else:
            newnet = True
        _trainMODIS(ocean,kwargs=kwargs,newnet=newnet)

        with open(lossFile, "wb") as f:
            loss = {"ermse": ocean.ermse,
                    "emae": ocean.emae,
                    "eme": ocean.eme,
                    "esqerr": ocean.esqerr}
            pickle.dump(loss, f)


    if doTest:
        _testMODIS(ocean)

        # if outlier were excluded, do an extra test with outliers included
        if (outliers > 0) and (K is None):
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
            ocean_out.expid = 'outlier.' + ocean_out.expid

            _testMODIS(ocean_out)


        
        if combinations:
            SummarizeCombinations(ocean,InputMaster,yrange=None,sortname='rmse')
      

