#!/usr/bin/env python3
"""
    Train the Dark Target Land Obs
"""

import os, sys
from   pyabc.abc_viirs         import ABC_DB_Land, _trainMODIS, _testMODIS, flatten_list
from   pyabc.abc_c6_aux           import SummarizeCombinations, SummaryPDFs


if __name__ == "__main__":
  # giantFile
  giantFile = '/nobackup/NNR/Training/002/giant_C002_10km_SNPP_v3.0_20221201.nc'
  
  # tymemax sets a truncation date when reading in giant file
  # string with format YYYYMMDD
  # None reads the entire datarecord
  tymemax = None

  # number of hidden layers
  nHLayers     = 1

  # number of nodes in hidden layers
  # None uses the default of 200 coded in nn.py  
  nHidden      = 200

  # do training on combinations of the inputs
  combinations = False

  # NN target variable names
#  Target       = ['aTau440','aTau470','aTau500','aTau550','aTau660','aTau870']
#  Target       = ['aTau550']
  Target       = ['aAE440','aAE470','aTau550','aAE660','aAE870','aAE1020','aAE1640']

  # surface albedo variable name
  # options are None, MCD43C1, MOD43BClimAlbedo  
  Albedo       = None #['MCD43C1'] #['MOD43BClimAlbedo']

  # number of K-folds or training
  # if None does not do K-folding, trains on entire dataset
  K            = 3 


  # Flags to Train of Test the DEEP BLUE DATASET
  doTrain      = True
  doTest       = True

  # experiment name
  expid        = 'candidate_8outputsAE_002'

  # Inputs that are always included
  # this can be None
#  Input_const  = ['SolarZenith','ScatteringAngle', 'GlintAngle','mRef412','mRef470','mRef660',
#                  'fdu','fcc','fss']
  Input_const  = None

  # Inputs that can be varied across combinations
  # if combinations flag is False, all of these inputs are used
  # if combinations flag is True, all possible combinations of these inputs
  # are tried
  Input_nnr    = ['SolarZenith','ScatteringAngle', 'GlintAngle',
                  'mRef412','mRef488','mRef550','mRef670','mRef865','mRef1240','mRef1640','mRef2250'] +\
                 ['mSre412','mSre488','mSre670'] +\
                 ['fdu','fcc','fss'] +\
                 ['ndvi'] +\
                 ['atype'] +\
                 ['cloud'] +\
                 ['algflag'] +\
                 ['colO3'] +\
                 ['water'] +\
                 ['pixel_elevation']
#                 ['BRDF470','BRDF550','BRDF650','BRDF850','BRDF1200','BRDF1600','BRDF2100']
#                 ['algflag']
#  Input_nnr =   ['BRDF470','BRDF550','BRDF650','BRDF850','BRDF1200','BRDF1600','BRDF2100']
#  Input_nnr    = ['mSre412','mSre470','mSre660']
#  'fdu','fcc','fss'] +\
  # Additional variables that the inputs are filtered by
  # standard filters are hardcoded in the abc_c6.py scripts
  aFilter      = ['aTau440','aTau470','aTau550','aTau660','aTau870','aTau1020','aTau1640'] +\
                 ['mSre412','mSre488','mSre670'] +\
                 ['colO3'] +\
                 ['water'] +\
                 ['pixel_elevation']
#                 ['BRDF470','BRDF550','BRDF650','BRDF850','BRDF1200','BRDF1600','BRDF2100']
#                 ['algflag'] 
  # ['BRDF470','BRDF550','BRDF650','BRDF850','BRDF1200','BRDF1600','BRDF2100']


  # --------------
  # End of Inputs
  # -------------

  # get satellite name from giantFile name
  sat = giantFile.split('_')[-3]

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
    deep = ABC_DB_Land(giantFile,Albedo=Albedo,verbose=1,aFilter=aFilter,tymemax=tymemax,cloud_thresh=0.7,
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
                        f_balance    = 0.35)


  # Do Training and Testing
  # ------------------------
  if doTrain:
    _trainMODIS(deep)

  if doTest:
    _testMODIS(deep)
    SummaryPDFs(deep,varnames=['mRef670','mSre488'])

    if combinations:
      SummarizeCombinations(deep,InputMaster,yrange=None,sortname='rmse')
      


