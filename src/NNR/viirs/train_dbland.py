#!/usr/bin/env python3
"""
    Train the Dark Target Land Obs
"""

import os, sys
from   pyabc.abc_viirs         import ABC_DB_Land, _trainMODIS, _testMODIS, flatten_list
from   pyabc.abc_c6_aux           import SummarizeCombinations, SummaryPDFs
import argparse
from   glob                    import glob

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

    # NN target variable names
    Target       = inputs['Target']

    # surface albedo variable name
    # options are None, MCD43C1, MOD43BClimAlbedo  
    Albedo       = inputs['Albedo']

    # number of K-folds or training
    # if None does not do K-folding, trains on entire dataset
    K            = inputs['K']

    # Flags to Train of Test the DEEP BLUE DATASET
    doTrain      = inputs['doTrain']
    doTest       = inputs['doTest']

    # experiment name
    expid        = inputs['expid']

    # Inputs that are always included
    # this can be None
    Input_const  = inputs['Input_const']

    # Inputs that can be varied across combinations
    # if combinations flag is False, all of these inputs are used
    # if combinations flag is True, all possible combinations of these inputs
    # are tried
    Input_nnr    = inputs['Input_nnr']

    # Inputs I want to the the log-transform of
    lInput_nnr = inputs['lInput_nnr']

    # Additional variables that the inputs are filtered by
    # standard filters are hardcoded in the abc_c6.py scripts
    aFilter      = inputs['aFilter']

    # fraction that defines whether a pixel is domniated by a species
    f_balance = inputs['f_balance']

    # flag to do both species and target AOD balancing
    q_balance = inputs['q_balance']

    # minimum number of points to have in a size bin for balancing
    # this is an adhoc parameter, but if it's too small, no obs will make
    # it through balancing procedure
    minN = inputs['minN']

    # --------------
    # End of Inputs
    # -------------

    # get satellite name from giantFile name
    if type(giantFile) is str:
        sat = giantFile.split('_')[-4]
    else:
        sat = giantFile[0].split('_')[-4]

    if sat == 'SNPP':
        retrieval    = 'VS_DB_LAND'
    if sat == 'NOAA20':
        retrieval    = 'VN20_DB_LAND'

    expid        = '{}_{}'.format(retrieval,expid)

    if Input_const is not None:
        InputMaster = list((Input_const,) + tuple(Input_nnr))      
    else:
        InputMaster = Input_nnr

    # Train/Test on full dataset
    # -------------------------------------
    if doTrain or doTest:
        deep = ABC_DB_Land(giantFile,aerFile=aerFile,Albedo=Albedo,verbose=1,aFilter=aFilter,tymemax=tymemax,cloud_thresh=0.7,
                       algflag=None)  
        # Initialize class for training/testing
        # ---------------------------------------------
        deep.setupNN(retrieval, expid,
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
                        minN         = minN)

    # Do Training and Testing
    # ------------------------
    if doTrain:
        _trainMODIS(deep)

    if doTest:
        _testMODIS(deep)
        SummaryPDFs(deep,varnames=['mRef670','mSre488'])

      if combinations:
          SummarizeCombinations(deep,InputMaster,yrange=None,sortname='rmse')
      


