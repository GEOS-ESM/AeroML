#!/usr/bin/env python
"""
    Train the Dark Target Ocean Obs
"""

import os, sys
from   pyabc.abc_c6               import ABC_Ocean, _trainMODIS, _testMODIS
from   pyabc.abc_c6_aux           import SummarizeCombinations
from   glob                       import glob
import argparse

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("inputs",
                        help="python file with dictionary of inputs")

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

    slvFile = []
    for sFile in inputs['slvFile']:
        slvFile += sorted(glob(sFile))

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
    doTrain      = inputs['doTrain']
    doTest       = inputs['doTest']

    # experiment name
    expid   = inputs['expid']  

    # Inputs that are always included
    # this can be None
#    Input_const  = ['SolarZenith','ScatteringAngle', 'GlintAngle',
#                  'mRef470','mRef550','mRef660', 'mRef870','mRef1200','mRef1600','mRef2100',
#                  'fdu','fcc','fss']
#    Input_const = None

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

    # --------------
    # End of Inputs
    # -------------

    # get satellite name from giantFile name
    if type(giantFile) is str:
        gFile = giantFile
    else:
        gFile = giantFile[0]
    if 'terra' in os.path.basename(gFile).lower():
        sat      = 'Terra'
    elif 'aqua' in os.path.basename(gFile).lower():
        sat      = 'Aqua'

    if sat == 'Terra':
        retrieval    = 'MOD_OCEAN'
    if sat == 'Aqua':
        retrieval    = 'MYD_OCEAN'

    expid        = '{}_{}'.format(retrieval,expid)

    if Input_const is not None:
        InputMaster = list((Input_const,) + tuple(Input_nnr))
    else:
        InputMaster = Input_nnr

    # Train/Test on full dataset
    # -------------------------------------
    if doTrain or doTest:
        ocean = ABC_Ocean(giantFile,aerFile=aerFile,slvFile=slvFile,
                      Albedo=Albedo,verbose=1,aFilter=aFilter,tymemax=tymemax,
                      cloud_thresh=cloud_thresh,outliers=outliers,
                      logoffset=logoffset,laod=laod,scale=scale)  

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
                      minN         = minN,
                      fignore      = fignore,
                      nbins        = nbins)


    # Do Training and Testing
    # ------------------------
    if doTrain:
        _trainMODIS(ocean)

    if doTest:
        _testMODIS(ocean)

        # if outlier were excluded, do an extra test with outliers included
        if (outliers > 0) and (K is None):
            ocean_out = ABC_Ocean(giantFile,aerFile=aerFile,slvFile=slvFile,
                              Albedo=Albedo,verbose=1,aFilter=aFilter,tymemax=tymemax,
                              cloud_thresh=cloud_thresh,outliers=-1,
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
      

