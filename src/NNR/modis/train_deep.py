#!/usr/bin/env python
"""
    Train the Dark Target Land Obs
"""

import os, sys
from   pyabc.abc_c6               import ABC_Deep, _trainMODIS, _testMODIS
from   pyabc.abc_c6_aux           import SummarizeCombinations
from   pyabc.abc_c6               import ABC_DEEP_COMP, ABC_DBDT_INT
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
    doTest_extra = inputs['doTest_extra']

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
        retrieval    = 'MOD_DEEP'
    if sat == 'Aqua':
        retrieval    = 'MYD_DEEP'


    expid        = '{}_{}'.format(retrieval,expid)

    if Input_const is not None:
        InputMaster = list((Input_const,) + tuple(Input_nnr))      
    else:
        InputMaster = Input_nnr

    # Train/Test on full dataset
    # -------------------------------------
    if doTrain or doTest:
      deep = ABC_Deep(giantFile,aerFile=aerFile,slvFile=slvFile,
                      useLAND=False,Albedo=Albedo,verbose=1,aFilter=aFilter,tymemax=tymemax,
                      cloud_thresh=cloud_thresh,outliers=outliers,
                      logoffset=logoffset,laod=laod,scale=scale)  

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
                          q_balance_enhance = q_balance_enhance,
                          minN         = minN,
                          fignore      = fignore,
                          nbins        = nbins)


    # Do Training and Testing
    # ------------------------
    if doTrain:
        _trainMODIS(deep)

    if doTest:
        _testMODIS(deep)

        # if outlier were excluded, do an extra test with outliers included
        if (outliers > 0) and (K is None):
            deep_out = ABC_Deep(giantFile,aerFile=aerFile,slvFile=slvFile,
                      useLAND=False,Albedo=Albedo,verbose=1,aFilter=aFilter,tymemax=tymemax,
                      cloud_thresh=cloud_thresh,outliers=-1,
                      logoffset=logoffset,laod=laod,scale=scale)

            deep_out.setupNN(retrieval, expid,
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

            deep_out.iTest[deep.outValid][deep.iTrain] = False
            deep_out.expid = 'outlier.' + deep_out.expid

            _testMODIS(deep_out)


        if combinations:
            SummarizeCombinations(deep,InputMaster,yrange=None,sortname='rmse')
      


    # Test on DB-DT Intersection
    #-----------------------------
    if doTest_extra:
        deep_int = ABC_DBDT_INT(giantFile,Albedo=Albedo,useDEEP=True,testDEEP=True,verbose=1,aFilter=aFilter,tymemax=tymemax)  
        if deep_int.nobs >0:
            deep_int.setupNN(retrieval, expid,
                          nHidden      = nHidden,
                          nHLayers     = nHLayers,
                          combinations = combinations,
                          Input_const  = Input_const,
                          Input_nnr    = Input_nnr,                                         
                          Target       = Target,                      
                          K            = K)  

            deep_int.plotdir = deep_int.outdir + '/DEEP_INT/'
            _testMODIS(deep_int)
            if combinations:
                SummarizeCombinations(deep_int,InputMaster,yrange=None,sortname='rmse')

            deep_int = ABC_DBDT_INT(giantFile,Albedo=Albedo,useDEEP=True,testDEEP=False,verbose=1,aFilter=aFilter,tymemax=tymemax)  

            deep_int.setupNN(retrieval, expid,
                          nHidden      = nHidden,
                          nHLayers     = nHLayers,
                          combinations = combinations,
                          Input_const  = Input_const,
                          Input_nnr    = Input_nnr,                                         
                          Target       = Target,                      
                          K            = K)  

            deep_int.plotdir = deep_int.outdir + '/DEEP_INT/'

            SummaryPDFs(deep_int,doInt=True)  



    # Test on DEEP BLUE Complement
    # ---------------------------------------------  
    if doTest_extra:
        deep_comp = ABC_DEEP_COMP(giantFile,useLAND=False,noLANDref=False,Albedo=Albedo,verbose=1,aFilter=aFilter,tymemax=tymemax)
        if deep_comp.nobs >0:
            # Initialize class for training/testing
            # ---------------------------------------------
            deep_comp.setupNN(retrieval, expid,
                          nHidden      = nHidden,
                          nHLayers     = nHLayers,
                          combinations = combinations,
                          Input_const  = Input_const,
                          Input_nnr    = Input_nnr,                                         
                          Target       = Target,                      
                          K            = K)  

            deep_comp.plotdir = deep_comp.outdir + '/DEEP_COMP/'
            _testMODIS(deep_comp)
            SummaryPDFs(deep_comp,varnames=['mRef660','mSre470'])  

            if combinations:
                SummarizeCombinations(deep_comp,InputMaster,yrange=None,sortname='rmse')
  
