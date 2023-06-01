#!/usr/bin/env python
"""
    Train the Dark Target Ocean Obs
"""

import os, sys
from   abc_c6               import ABC_Ocean, _trainMODIS, _testMODIS, flatten_list
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

  # NN target variable name
#  Target       = ['aTau440','aTau470','aTau500','aTau550','aTau660','aTau870']
  Target       = ['aAE440','aAE470','aAE500','aTau550','aAE660','aAE870']
#  Target       = ['aTau440','aTau550','aTau870']

  # surface albedo variable name
  # options are None, CoxMunkLUT, or CxAlbedo
  # if CoxMunkLUT one needs to provide the coxmunk_lut option to ABC_Ocean, 
  # otherwise default is used (default = '/nobackup/NNR/Misc/coxmunk_lut.npz')
  # if CxAlbedo is used, need to provide a *npz file with CxAlbedo precalculated
  Albedo       = None #['CxAlbedo']

  # number of K-folds or training
  # if None does not do K-folding, trains on entire dataset
  K            = None

  # Flags to Train or Test the DARK TARGET DATASET
  doTrain      = True
  doTest       = True

  # experiment name
  expid        = 'candidate_6outputsAE_061'  

  # Inputs that are always included
  # this can be None
#  Input_const  = ['SolarZenith','ScatteringAngle', 'GlintAngle',
#                  'mRef470','mRef550','mRef660', 'mRef870','mRef1200','mRef1600','mRef2100',
#                  'fdu','fcc','fss']
  Input_const = None

  # Inputs that can be varied across combinations
  # if combinations flag is False, all of these inputs are used
  # if combinations flag is True, all possible combinations of these inputs
  # are tried
  Input_nnr    = ['SolarZenith','ScatteringAngle', 'GlintAngle',
                  'mRef470','mRef550','mRef660', 'mRef870','mRef1200','mRef1600','mRef2100',
                  'fdu','fcc','fss'] 
#                 ['wind']

#  Input_nnr    = ['CxAlbedo470','CxAlbedo550','CxAlbedo660','CxAlbedo870','CxAlbedo1200','CxAlbedo1600','CxAlbedo2100']
#  Input_nnr    = ['wind']

  # Additional variables that the inputs are filtered by
  # standard filters are hardcoded in the abc_c6.py scripts  
  aFilter      = ['aTau440','aTau470','aTau500','aTau550','aTau660','aTau870']

  # --------------
  # End of Inputs
  # -------------

  # get satellite name from giantFile name
  if 'terra' in os.path.basename(giantFile).lower():
      sat      = 'Terra'
  elif 'aqua' in os.path.basename(giantFile).lower():
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
    ocean = ABC_Ocean(giantFile,Albedo=Albedo,verbose=1,aFilter=aFilter,tymemax=tymemax)  
    # Initialize class for training/testing
    # ---------------------------------------------
    ocean.setupNN(retrieval, expid,
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
    _trainMODIS(ocean)

  if doTest:
    _testMODIS(ocean)
    SummaryPDFs(ocean,varnames=['mRef870','mRef660'])
    if combinations:
      SummarizeCombinations(ocean,InputMaster,yrange=None,sortname='slope')
      

