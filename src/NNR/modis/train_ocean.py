#!/usr/bin/env python
"""
    Train the Dark Target Ocean Obs
"""

import os, sys
from   pyabc.abc_c6               import ABC_Ocean, _trainMODIS, _testMODIS, flatten_list
from   pyabc.abc_c6_aux           import SummarizeCombinations, SummaryPDFs
from   glob                       import glob
import argparse

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("inputs",
                        help="python file with dictionary of inputs")

    parser.add_argument("--notrain",action='store_true',
                        help="don't do training")

    parser.add_argument("--notest",action='store_true',
                        help="don't do testing")    

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
    if args.notrain:
        doTrain = False
    else:
        doTrain = True

    if args.notest:
        doTest = False
    else:
        doTest = True

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
    lInput_nnr = ['mRef412','mRef440','mRef470','mRef550','mRef660', 'mRef870','mRef1200','mRef1600','mRef2100',
                  'fdu','fcc','fss']

    # Additional variables that the inputs are filtered by
    # standard filters are hardcoded in the abc_c6.py scripts  
    aFilter      = ['aTau440','aTau470','aTau500','aTau550','aTau660','aTau870']

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
                      Albedo=Albedo,verbose=1,aFilter=aFilter,tymemax=tymemax)  
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
                      lInput_nnr   = lInput_nnr)


    # Do Training and Testing
    # ------------------------
    if doTrain:
        _trainMODIS(ocean)

    if doTest:
        _testMODIS(ocean)
        SummaryPDFs(ocean,varnames=None)
        if combinations:
            SummarizeCombinations(ocean,InputMaster,yrange=None,sortname='rmse')
      

