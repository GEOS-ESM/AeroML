#!/usr/bin/env python3
"""
    Train the Dark Target Land Obs
"""

import os, sys
from   abc_c6               import ABC_Land, ABC_LAND_COMP, ABC_DBDT_INT, _trainMODIS, _testMODIS, flatten_list
from   abc_c6_aux           import SummarizeCombinations, SummaryPDFs


if __name__ == "__main__":
  # giantFile
  giantFile = '/nobackup/NNR/Training/061/giant_C061_10km_Terra_v3.0_20211231.nc'

  # tymemax sets a truncation date when reading in giant file
  # string with format YYYYMMDD
  # None reads the entire datarecord
  tymemax = None

  # number of hidden layers
  nHLayers     = 1

  # number of nodes in hidden layers
  # None uses the default of 200 coded in nn.py
  nHidden      = None

  # do training on combinations of the inputs
  combinations = False

  # NN target variable names
#  Target       = ['aTau440','aTau470','aTau500','aTau550','aTau660','aTau870']
#  Target       = ['aTau550']
  Target       = ['aAE440','aAE470','aAE500','aTau550','aAE660','aAE870']
#  Target       = ['aTau440','aTau550','aTau870']

  # surface albedo variable name
  # options are MCD43C1, MOD43BClimAlbedo
  Albedo       = None #['MCD43C1'] #['MOD43BClimAlbedo']

  # number of K-folds or training
  # if None does not do K-folding, trains on entire dataset
  K            = None


  # Flags to Train or Test the DARK TARGET DATASET
  doTrain      = True
  doTest       = True
  doTest_extra = False

  # experiment name
  expid        = 'candidate_mSre_6outputsAE_061'

  # Inputs that are always included
  # this can be set to None
  # Must set to None if not doing combinations and put all your inputs in the Input_nnr variable
#  Input_const  = ['ScatteringAngle', 'GlintAngle','SolarZenith',
#                  'mRef412','mRef440','mRef470','mRef550','mRef660', 'mRef870','mRef1200','mRef1600','mRef2100',
#                  'fdu','fcc','fss']

  Input_const = None

  # Inputs that can be varied across combinations
  # if combinations flag is False, all of these inputs are used
  # if combinations flag is True, all possible combinations of these inputs
  # are tried  
  Input_nnr    = ['SolarZenith','ScatteringAngle', 'GlintAngle',
                  'mRef412','mRef440','mRef470','mRef550','mRef660', 'mRef870','mRef1200','mRef1600','mRef2100',
                 'fdu','fcc','fss','mSre470','mSre660','mSre2100']
#  Input_nnr =   ['BRDF470','BRDF550','BRDF650','BRDF850','BRDF1200','BRDF1600','BRDF2100']
#  Input_nnr = ['mSre470','mSre660','mSre2100']


  # Additional variables that the inputs are filtered by
  # standard filters are hardcoded in the abc_c6.py scripts  
  aFilter      = ['aTau440','aTau470','aTau500','aTau550','aTau660','aTau870']+\
                 ['mSre470','mSre660','mSre2100']          
#                 ['BRDF470','BRDF550','BRDF650','BRDF850','BRDF1200','BRDF1600','BRDF2100']+\
#                 ['mSre470','mSre660','mSre2100']

  # --------------
  # End of Inputs
  # -------------

  # get satellite name from giantFile name
  if 'terra' in os.path.basename(giantFile).lower():
      sat      = 'Terra'
  elif 'aqua' in os.path.basename(giantFile).lower():
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
    land = ABC_Land(giantFile,Albedo=Albedo,verbose=1,aFilter=aFilter,tymemax=tymemax)  
    # Initialize class for training/testing
    # ---------------------------------------------
    land.setupNN(retrieval, expid,
                        nHidden      = nHidden,
                        nHLayers     = nHLayers,
                        combinations = combinations,
                        Input_const  = Input_const,
                        Input_nnr    = Input_nnr,                                         
                        Target       = Target,                      
                        K            = K)



  # Do Training and Testing
  # ------------------------
  if doTrain:
    _trainMODIS(land)

  if doTest:
    _testMODIS(land)
    SummaryPDFs(land)
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
        SummaryPDFs(land_int,doInt=True)  
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
        SummaryPDFs(land_comp)    
        if combinations:
            SummarizeCombinations(land_comp,InputMaster,yrange=None,sortname='rmse')
  
