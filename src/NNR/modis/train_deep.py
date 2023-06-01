#!/usr/bin/env python
"""
    Train the Dark Target Land Obs
"""

import os, sys
from   abc_c6               import ABC_Deep, _trainMODIS, _testMODIS, flatten_list
from   abc_c6_aux           import SummarizeCombinations, SummaryPDFs
from   abc_c6               import ABC_DEEP_COMP, ABC_DBDT_INT


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
#  Target       = ['aAE440','aTau550','aAE870']
#  Target       = ['aTau440','aTau550','aTau870']

  # surface albedo variable name
  # options are None, MCD43C1, MOD43BClimAlbedo  
  Albedo       = None #['MCD43C1'] #['MOD43BClimAlbedo']

  # number of K-folds or training
  # if None does not do K-folding, trains on entire dataset
  K            = None  


  # Flags to Train of Test the DEEP BLUE DATASET
  doTrain      = True
  doTest       = True
  doTest_extra = False

  # experiment name
  expid        = 'candidate_mSre_6outputsAE_061'

  # Inputs that are always included
  # this can be None
#  Input_const  = ['SolarZenith','ScatteringAngle', 'GlintAngle','mRef412','mRef470','mRef660',
#                  'fdu','fcc','fss']
  Input_const  = None

  # Inputs that can be varied across combinations
  # if combinations flag is False, all of these inputs are used
  # if combinations flag is True, all possible combinations of these inputs
  # are tried
  Input_nnr    = ['SolarZenith','ScatteringAngle', 'GlintAngle','mRef412','mRef470','mRef660',
                  'fdu','fcc','fss']+\
                 ['mSre412','mSre470','mSre660']         
#  Input_nnr =   ['BRDF470','BRDF550','BRDF650','BRDF850','BRDF1200','BRDF1600','BRDF2100']
#  Input_nnr    = ['mSre412','mSre470','mSre660']

  # Additional variables that the inputs are filtered by
  # standard filters are hardcoded in the abc_c6.py scripts
#  aFilter      = ['aTau440','aTau470','aTau500','aTau550','aTau660','aTau870'] +\
  aFilter      = ['aTau440','aTau550','aTau870'] +\
                 ['mSre412','mSre470','mSre660'] #+\
#                 ['BRDF470','BRDF550','BRDF650','BRDF850','BRDF1200','BRDF1600','BRDF2100']
 
  # ['BRDF470','BRDF550','BRDF650','BRDF850','BRDF1200','BRDF1600','BRDF2100']


  # --------------
  # End of Inputs
  # -------------

  # get satellite name from giantFile name
  if 'terra' in os.path.basename(giantFile).lower():
      sat      = 'Terra'
  elif 'aqua' in os.path.basename(giantFile).lower():
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
    deep = ABC_Deep(giantFile,useLAND=False,Albedo=Albedo,verbose=1,aFilter=aFilter,tymemax=tymemax)  
    # Initialize class for training/testing
    # ---------------------------------------------
    deep.setupNN(retrieval, expid,
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
    _trainMODIS(deep)

  if doTest:
    _testMODIS(deep)
    SummaryPDFs(deep,varnames=['mRef660','mSre470'])

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
  
