#!/usr/bin/env python3
"""
    Train the Dark Target Land Obs
"""

import os, sys
from   pyabc.abc_c6               import ABC_Land, ABC_LAND_COMP, ABC_DBDT_INT, _trainMODIS, _testMODIS
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

    # NN target variable names
    Target = inputs['Target']

    # surface albedo variable name
    # options are MCD43C1, MOD43BClimAlbedo
    Albedo       = inputs['Albedo']

    # number of K-folds or training
    # if None does not do K-folding, trains on entire dataset
    K            = inputs['K']

    # Flags to Train or Test the DARK TARGET DATASET
    doTrain      = inputs['doTrain']
    doTest       = inputs['doTest']
    doTest_extra = inputs['doTest_extra']


    # experiment name
    expid   = inputs['expid']

    # Inputs that are always included
    # this can be set to None
    # Must set to None if not doing combinations and put all your inputs in the Input_nnr variable
#  Input_const  = ['ScatteringAngle', 'GlintAngle','SolarZenith',
#                  'mRef412','mRef440','mRef470','mRef550','mRef660', 'mRef870','mRef1200','mRef1600','mRef2100',
#                  'fdu','fcc','fss']

    Input_const = inputs['Input_const']

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
        retrieval    = 'MOD_LAND'
    if sat == 'Aqua':
        retrieval    = 'MYD_LAND'      


    expid        = '{}_{}'.format(retrieval,expid)

    if Input_const is not None:
        InputMaster = list((Input_const,) + tuple(Input_nnr))      
    else:
        InputMaster = Input_nnr

    # Train/Test on full dataset
    # -------------------------------------
    if doTrain or doTest:
        land = ABC_Land(giantFile,aerFile=aerFile,slvFile=slvFile,
                      Albedo=Albedo,verbose=1,aFilter=aFilter,tymemax=tymemax,
                      cloud_thresh=cloud_thresh,outliers=outliers,
                      logoffset=logoffset,laod=laod,scale=scale) 

        # Initialize class for training/testing
        # ---------------------------------------------
        land.setupNN(retrieval, expid,
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



    # Do Training and Testing
    # ------------------------
    if doTrain:
        _trainMODIS(land)

    if doTest:
        _testMODIS(land)

        # if outlier were excluded, do an extra test with outliers included
        if (outliers > 0) and (K is None):
            land_out = ABC_Land(giantFile,aerFile=aerFile,slvFile=slvFile,
                      Albedo=Albedo,verbose=1,aFilter=aFilter,tymemax=tymemax,
                      cloud_thresh=cloud_thresh,outliers=-1,
                      logoffset=logoffset,laod=laod,scale=scale)

            land_out.setupNN(retrieval, expid,
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

            land_out.iTest[land.outValid][land.iTrain] = False
            land_out.expid = 'outlier.' + land_out.expid

            _testMODIS(land_out)


        if combinations:
            SummarizeCombinations(land,InputMaster,yrange=None,sortname='rmse')
      


    # Test on DB-DT Intersection
    #-----------------------------
    if doTest_extra:
        land_int = ABC_DBDT_INT(giantFile,Albedo=Albedo,useDEEP=False,testDEEP=False,verbose=1,aFilter=aFilter,tymemax=tymemax)  
        if land_int.nobs > 0:
            land_int.setupNN(retrieval, expid,
                      nHidden      = nHidden,
                      nHLayers     = nHLayers,
                      combinations = combinations,
                      Input_const  = Input_const,
                      Input_nnr    = Input_nnr,                                         
                      Target       = Target,                      
                      K            = K)  

            land_int.plotdir = land_int.outdir + '/LAND_INT/'
            _testMODIS(land_int)
            if combinations:
                SummarizeCombinations(land_int,InputMaster,yrange=None,sortname='rmse')
  

    # Test on Land Complement
    #-----------------------------
    if doTest_extra:
        land_comp = ABC_LAND_COMP(giantFile,Albedo=Albedo,useDEEP=False,verbose=1,aFilter=aFilter,tymemax=tymemax)  
        if land_comp.nobs > 0:
            land_comp.setupNN(retrieval, expid,
                      nHidden      = nHidden,
                      nHLayers     = nHLayers,
                      combinations = combinations,
                      Input_const  = Input_const,
                      Input_nnr    = Input_nnr,                                         
                      Target       = Target,                      
                      K            = K)  

            land_comp.plotdir = land_comp.outdir + '/LAND_COMP/'
            _testMODIS(land_comp)
            if combinations:
                SummarizeCombinations(land_comp,InputMaster,yrange=None,sortname='rmse')
  
