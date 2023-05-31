#!/usr/bin/env python3
"""
    Train the Dark Target Ocean Obs
"""

import os, sys
from   pyabc.abc_viirs            import ABC_DB_Ocean, _trainMODIS, _testMODIS, flatten_list
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
  nHidden      = None

  # do training on combinations of the inputs
  combinations = False

  # NN target variable name
#  Target       = ['aTau440','aTau470','aTau500','aTau550','aTau660','aTau870']
  Target       = ['aAE440','aAE470','aAE500','aTau550','aAE660','aAE870']

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
  expid        = 'candidate_6outputsAE_011'  
  expid        = 'testing'

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
                  'mRef412','mRef488','mRef550','mRef670', 'mRef865','mRef1240','mRef1640','mRef2250',
                  'fdu','fcc','fss'] +\
                 ['wind'] +\
                 ['cloud'] +\
                 ['algflag'] +\
                 ['atype'] +\
                 ['colO3'] +\
                 ['water']                  

#  Input_nnr    = ['CxAlbedo470','CxAlbedo550','CxAlbedo660','CxAlbedo870','CxAlbedo1200','CxAlbedo1600','CxAlbedo2100']
#  Input_nnr    = ['wind']

  # Additional variables that the inputs are filtered by
  # standard filters are hardcoded in the abc_c6.py scripts  
  aFilter      = ['aTau440','aTau470','aTau500','aTau550','aTau660','aTau870'] +\
                 ['colO3'] +\
                 ['water']

  # --------------
  # End of Inputs
  # -------------

  # get satellite name from giantFile name
  sat = giantFile.split('_')[-3]

  if sat == 'SNPP':
    retrieval    = 'VS_DB_OCEAN'
  if sat == 'NOAA20':
    retrieval    = 'VN20_DB_OCEAN'

  expid        = '{}_{}'.format(retrieval,expid)

  if Input_const is not None:
    InputMaster = list((Input_const,) + tuple(Input_nnr))
  else:
    InputMaster = Input_nnr

  # Train/Test on full dataset
  # -------------------------------------
  if doTrain or doTest:
    ocean = ABC_DB_Ocean(giantFile,Albedo=Albedo,verbose=1,aFilter=aFilter,tymemax=tymemax,cloud_thresh=1)  
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
    SummaryPDFs(ocean,varnames=['mRef865','mRef488'])
    if combinations:
      SummarizeCombinations(ocean,InputMaster,yrange=None,sortname='slope')
      

