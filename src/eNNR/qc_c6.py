"""
   This module implements a Neural Net based MODIS Collection 6 Neural Net Retrieval.

   Arlindo da Silva, June 2015.

"""

import os, sys

from functools import reduce

from   numpy                import  c_ as cat
from   numpy                import  random, sort, pi, load, cos, log, std, exp
from   numpy                import  reshape, arange, ones, zeros, interp, sqrt
from   numpy                import  meshgrid, concatenate, squeeze
import numpy                as      np
from   giant                import  MISSING, LAND, OCEAN, DEEP

from   brdf                 import rtlsReflectance
from   mcd43c               import BRDF

# ------
MODVARNAMES = {'mRef470': 'MOD04 470 nm Reflectance',
               'mRef550': 'MOD04 550 nm Reflectance',
               'mRef660': 'MOD04 660 nm Reflectance',
               'mRef870': 'MOD04 870 nm Reflectance',
               'mRef1200': 'MOD04 1200 nm Reflectance',
               'mRef1600': 'MOD04 1600 nm Reflectance',
               'mRef2100': 'MOD04 2100 nm Reflectance'}

MYDVARNAMES = {'mRef470': 'MYD04 470 nm Reflectance',
               'mRef550': 'MYD04 550 nm Reflectance',
               'mRef660': 'MYD04 660 nm Reflectance',
               'mRef870': 'MYD04 870 nm Reflectance',
               'mRef1200': 'MYD04 1200 nm Reflectance',
               'mRef1600': 'MYD04 1600 nm Reflectance',
               'mRef2100': 'MYD04 2100 nm Reflectance'}

VARNAMES    = {'cloud': 'MOD04 Cloud Fraction',
               'ScatteringAngle': 'Scattering Angle',
               'GlintAngle': 'Glint Angle',
               'AMF': 'Air Mass Factor',
               'SolarZenith': 'Solar Zenith Angle',
               'CoxMunkLUT': 'Cox-Munk White Sky Albedo',
               'COxMunkBRF': 'Cox-Munk Bidirectional Surface Reflectance',
               'MOD43BClimAlbedo': 'MOD43B Albedo Climatology',
               'fdu': 'MERRA2 Fraction Dust Aerosol',
               'fcc': 'MERRA2 Fraction Carbonaceous Aerosol',
               'fsu': 'MERRA2 Fraction Sulfate Aerosol',
               'year': 'Year'}

#--------------------------------------------------------------------------------------
class QC(object):

    """
    Common Quality Control Functionality Classes
    """

    def __init__(self,fname,Albedo,coxmunk_lut=None):

        # Get Auxiliary Data
        # ------------------
        self.setfnameRoot(fname)
        self.setWind()
        self.setAlbedo(Albedo,coxmunk_lut=coxmunk_lut)
        self.setSpecies()
        self.setNDVI()

    def setfnameRoot(self,fname):

        dirn = os.path.dirname(fname)
        base = os.path.basename(fname)
            
        if self.sat == 'Aqua':
            self.fnameRoot = dirn + '/myd_' + base.split('.')[0]
        elif self.sat == 'Terra':
            self.fnameRoot = dirn + '/mod_' + base.split('.')[0]
        
    def setWind(self):
        """
        Read in wind data.
        """
        self.wind = load(self.fnameRoot + "_MERRA2.npz")['wind']
        self.variables.append('wind')
        self.Wind = '' #need this for backwards compatibility

    def setAlbedo(self,Albedo,coxmunk_lut=None):
        """
        Define wind speed dependent ocean albedo.
        """
        if Albedo is not None:
          for albedo in Albedo:
            if albedo == 'CoxMunkLUT':
              self.getCoxMunk(coxmunk_lut) 
              self.variables.append(albedo)    
            elif albedo == 'MCD43C1':
              self.setBRDF()     
            elif albedo == 'CxAlbedo':
              self.setCoxMunkBRF(albedo)
            else:
              self.__dict__[albedo] = squeeze(load(self.fnameRoot+'_'+albedo+'.npz')["albedo"])
              self.variables.append(albedo)

    def setSpecies(self):
        """
        Read in Aerosol Fractional Composition.
        """
        names = ('fdu','fss','fcc','fsu')
        for name in names:
            self.__dict__[name] = load(self.fnameRoot + "_MERRA2.npz")[name]
            self.variables.append(name)

    def setCoxMunkBRF(self,albedo):
        """
        Read in Cox Munk Bidirectional surface reflectance.
        """
        npz = load(self.fnameRoot+'_CoxMunkBRF.npz')
        for name in npz:
            self.__dict__[name] = squeeze(npz[name])
            self.variables.append(name)

    def setBRDF(self):
        """
        Read in MCD43C1 BRDF
        Calculate bidirectional surface reflectance
        """
        brdf = BRDF(self.nobs)
        names = ('BRDFvis','BRDFnir','BRDF470','BRDF550',
                 'BRDF650','BRDF850','BRDF1200','BRDF1600',
                 'BRDF2100')
        for name in brdf.__dict__:
            brdf.__dict__[name] = load(self.fnameRoot + "_MCD43C1.npz")[name]

        for name in names:
            ch = name[4:]
            Kiso = brdf.__dict__['Riso'+ch]
            Kvol = brdf.__dict__['Rvol'+ch]
            Kgeo = brdf.__dict__['Rgeo'+ch]
            self.__dict__[name] = rtlsReflectance(Kiso,Kgeo,Kvol,
                                                  self.SolarZenith,self.SensorZenith,
                                                  self.SolarAzimuth,self.SensorAzimuth)
            self.variables.append(name)    


    def setNDVI(self):
        """
        Read in NDVI
        """
        names = ('NDVI','EVI','NIRref')
        for name in names:
          self.__dict__[name] = load(self.fnameRoot + "_NDVI.npz")[name]
          self.variables.append(name)

    def outlierRemoval(self,outliers):
        """
        Outlier removal based on log-transformed AOD
        """
        if outliers > 0.:
            d = log(self.mTau550[self.iValid]+0.01) - log(self.aTau550[self.iValid]+0.01)
            if self.verbose>0:
                print(("Outlier removal: %d   sig_d = %f  nGood=%d "%(-1,std(d),d.size)))
            for iter in range(3):
                iValid = (abs(d)<outliers*std(d))
                self.iValid[self.iValid] = iValid
                d = log(self.mTau550[self.iValid]+0.01) - log(self.aTau550[self.iValid]+0.01)
                if self.verbose>0:
                    print(("Outlier removal: %d   sig_d = %f  nGood=%d "%(iter,std(d),d.size)))
              
    def angleTranform(self):            
        """
        Angle transforms: for NN work we work with cosine of angles
        """
        
        self.ScatteringAngle = cos(self.ScatteringAngle*pi/180.0) 
        self.SensorAzimuth   = cos(self.SensorAzimuth*pi/180.0)   
        self.SensorZenith    = cos(self.SensorZenith*pi/180.0)    
        self.SolarAzimuth    = cos(self.SolarAzimuth*pi/180.0)    
        self.SolarZenith     = cos(self.SolarZenith*pi/180.0)     
        self.GlintAngle      = cos(self.GlintAngle*pi/180.0)      
        self.AMF             = (1/self.SolarZenith) + (1/self.SensorZenith)
        self.variables.append('AMF')

    def setYear(self):
        self.year = np.array([t.year for t in self.tyme])
        self.variables.append('year')

    def addFilter(self,aFilter):
        if aFilter is not None:
          filters = []
          for f in aFilter:
            filters.append(self.__dict__[f]>0)
            
          oiValid = reduce(lambda x,y: x&y,filters)
          self.iValid = self.iValid & oiValid

#....................................
class QC_OCEAN (OCEAN,QC):

    def __init__ (self,fname, 
                  coxmunk_lut='/nobackup/NNR/Misc/coxmunk_lut.npz',
                  outliers=3., 
                  laod=True, 
                  verbose=0,
                  cloud_thresh=0.70,
                  glint_thresh=40.0,
                  Albedo=None,
                  aFilter=None):
        """
        Initializes QC for the MODIS Ocean algorithm.

        On Input,

        fname   ---  file name for the CSV file with the co-located MODIS/AERONET
                     data (see class OCEAN)
        outliers --  number of standard deviations for outlinear removal.
        laod    ---  if True, targets are log-transformed AOD, log(Tau+0.01)

        Reads in two Albedo variables
              albedo - cox munk lut that parameterizes albedo with wind speed
                                        Requires coxmunk_lut npz file.
              BRF - cox munk bidirection reflectance computed with VLIDORT
                                        and stored in npz
                                        Requires a NPZ file with the data.
              Both require a wind speed npz file.
        """

        self.verbose = verbose
        self.laod    = laod

        OCEAN.__init__(self,fname) # initialize superclass

        # Get Auxiliary Data
        QC.__init__(self,fname,Albedo,coxmunk_lut=coxmunk_lut)

        # Q/C
        # ---
        self.iValid = (self.qa>0) & \
                      (self.aTau470 > -0.01) &\
                      (self.aTau550 > -0.01) &\
                      (self.aTau660 > -0.01) &\
                      (self.aTau870 > -0.01) &\
                      (self.mTau470 > -0.01) &\
                      (self.mTau550 > -0.01) &\
                      (self.mTau660 > -0.01) &\
                      (self.mTau870 > -0.01) &\
                      (self.mRef470 > 0.0)   &\
                      (self.mRef550 > 0.0)   &\
                      (self.mRef660 > 0.0)   &\
                      (self.mRef870 > 0.0)   &\
                      (self.mRef1200 > 0.0)  &\
                      (self.mRef1600 > 0.0)  &\
                      (self.mRef2100 > 0.0)  &\
                      (self.cloud <cloud_thresh) &\
                      (self.cloud > 0)           &\
                      (self.GlintAngle != MISSING ) &\
                      (self.GlintAngle > glint_thresh) 

        # Filter by additional variables
        # ------------------------------
        self.addFilter(aFilter)

        # glint_thresh > 40 is a bit redundant b/c MOD04 should already give these a qa==0 or
        # does not retrieve.  However, there are a few cases (~200) where this does not happen.
        # the GlingAngle is very close to 40, greater than 38.  Not sure why these get through.

        # Outlier removal based on log-transformed AOD
        # --------------------------------------------
        self.outlierRemoval(outliers)
              
        # Reduce the Dataset
        # --------------------
        self.reduce(self.iValid)                    
        self.iValid = ones(self.lon.shape).astype(bool)
            
        # Angle transforms: for NN work we work with cosine of angles
        # -----------------------------------------------------------
        self.angleTranform()

        # Year
        #-------
        self.setYear()

#----------------------------------------------------------------------------    

class QC_LAND (LAND,QC):

    def __init__ (self, fname,
                  Albedo=None,
                  alb_max = 0.25,
                  outliers=3.,
                  laod=True,
                  verbose=0,
                  cloud_thresh=0.70,
                  aFilter=None):
        """
        Initializes QC for the MODIS Land (Dark Target) algorithm.

        On Input,

        fname   ---  file name for the CSV file with the co-located MODIS/AERONET
                     data (see class OCEAN)

        Albedo  ---  albedo file name identifier; albedo file will be created
                     from this identifier (See below).
        outliers --  number of standard deviations for outlinear removal.
        laod    ---  if True, targets are log-transformed AOD, log(Tau+0.01)
        """

        self.verbose = verbose
        self.laod = laod

        LAND.__init__(self,fname)  # initialize superclass

        # Get Auxiliary Data
        QC.__init__(self,fname,Albedo)

        # Q/C: enforce QA=3 and albedo in (0,0.25), scattering angle<170
        # --------------------------------------------------------------
        self.iValid = (self.qa==3)                & \
                      (self.aTau470 > -0.01)      & \
                      (self.aTau550 > -0.01)      & \
                      (self.aTau660 > -0.01)      & \
                      (self.mTau470 > -0.01)      & \
                      (self.mTau550 > -0.01)      & \
                      (self.mTau660 > -0.01)      & \
                      (self.mTau2100> -0.01)      & \
                      (self.cloud<cloud_thresh)   & \
                      (self.cloud > 0)            &\
                      (self.ScatteringAngle<170.) & \
                      (self.mRef412 > 0)          & \
                      (self.mRef440 > 0)          & \
                      (self.mRef470 > 0)          & \
                      (self.mRef550 > 0)          & \
                      (self.mRef660 > 0)          & \
                      (self.mRef870 > 0)          & \
                      (self.mRef1200 > 0)         & \
                      (self.mRef1600 > 0)         & \
                      (self.mRef2100 > 0)         & \
                      (self.mSre470 >  0.0)       & \
                      (self.mSre660 >  0.0)       & \
                      (self.mSre2100>  0.0)       

        # Filter by additional variables
        # ------------------------------
        self.addFilter(aFilter)

        
        # Outlier removal based on log-transformed AOD
        # --------------------------------------------
        self.outlierRemoval(outliers)

        # Reduce the Dataset
        # --------------------
        self.reduce(self.iValid)                    
        self.iValid = ones(self.lon.shape).astype(bool)        

        # Angle transforms: for NN work we work with cosine of angles
        # -----------------------------------------------------------
        self.angleTranform()    

#........................................................
class QC_DEEP (DEEP,QC):

    def __init__ (self, fname,
                  useLAND=False,
                  Albedo=None,
                  outliers=3.,
                  laod=True,
                  verbose=0,
                  cloud_thresh=0.70,
                  aFilter=None):
        """
        Initializes QC for the MODIS Deep Blue algorithm.

        On Input,

        fname   ---  file name for the CSV file with the co-located MODIS/AERONET
                     data (see class OCEAN)

        Albedo  ---  albedo file name identifier; albedo file will be created
                     from this identifier (See below).
        outliers --  number of standard deviations for outlinear removal.
        laod    ---  if True, targets are log-transformed AOD, log(Tau+0.01)
        """

        self.verbose = verbose
        self.laod = laod

        DEEP.__init__(self,fname)  # initialize superclass

        # Get Auxiliary Data
        QC.__init__(self,fname,Albedo)

        # Q/C: enforce QA=3 and albedo in (0,0.25), scattering angle<170
        # --------------------------------------------------------------
        self.iValid = (self.qa==3)                & \
                      (self.aTau470 > -0.01)      & \
                      (self.aTau550 > -0.01)      & \
                      (self.aTau660 > -0.01)      & \
                      (self.mTau412 > -0.01)      & \
                      (self.mTau470 > -0.01)      & \
                      (self.mTau550 > -0.01)      & \
                      (self.mTau660 > -0.01)      & \
                      (self.cloud<cloud_thresh)   & \
                      (self.cloud > 0)            &\
                      (self.ScatteringAngle<170.) & \
                      (self.mRef412 > 0)          & \
                      (self.mRef470 > 0)          & \
                      (self.mRef660 > 0)          & \
                      (self.mSre412 >  0.0)       & \
                      (self.mSre470 >  0.0)       & \
                      (self.mSre660 >  0.0)      

        LANDref     = (self.mRef440 > 0)          & \
                      (self.mRef550 > 0)          & \
                      (self.mRef870 > 0)          & \
                      (self.mRef1200 > 0)         & \
                      (self.mRef1600 > 0)         & \
                      (self.mRef2100 > 0)         

        if useLAND:
          self.iValid = self.iValid & LANDref

        # Filter by additional variables
        # ------------------------------
        self.addFilter(aFilter)
        
        # Outlier removal based on log-transformed AOD
        # --------------------------------------------
        self.outlierRemoval(outliers)

        # Reduce the Dataset
        # --------------------
        self.reduce(self.iValid)                    
        self.iValid = ones(self.lon.shape).astype(bool)        

            
        # Angle transforms: for NN work we work with cosine of angles
        # -----------------------------------------------------------
        self.angleTranform()    

#----------------------------------------------------------------------------    

class QC_DBDT (LAND,QC):

    def __init__ (self, fname,
                  useDEEP = False,
                  Albedo=None,
                  outliers=3.,
                  laod=True,
                  verbose=0,
                  cloud_thresh=0.70,
                  aFilter=None):
        """
        Initializes QC for the combined MODIS Dark Target/Deep Blue algorithm.

        On Input,

        fname   ---  file name for the CSV file with the co-located MODIS/AERONET
                     data (see class OCEAN)

        Albedo  ---  albedo file name identifier; albedo file will be created
                     from this identifier (See below).
        outliers --  number of standard deviations for outlinear removal.
        laod    ---  if True, targets are log-transformed AOD, log(Tau+0.01)
        """

        self.verbose = verbose
        self.laod = laod

        LAND.__init__(self,fname)  # initialize superclass
        dbl = DEEP(fname)

        # Get Auxiliary Data
        QC.__init__(self,fname,Albedo)

        # Q/C: enforce QA=3 and scattering angle<170
        # Combines deep blue and dark target
        # --------------------------------------------------------------
        LANDiValid =  (self.qa==3)                & \
                      (self.aTau470 > -0.01)      & \
                      (self.aTau550 > -0.01)      & \
                      (self.aTau660 > -0.01)      & \
                      (self.mTau470 > -0.01)      & \
                      (self.mTau550 > -0.01)      & \
                      (self.mTau660 > -0.01)      & \
                      (self.cloud<cloud_thresh)   & \
                      (self.cloud > 0)            & \
                      (self.ScatteringAngle<170.) & \
                      (self.mRef412 > 0)          & \
                      (self.mRef440 > 0)          & \
                      (self.mRef470 > 0)          & \
                      (self.mRef550 > 0)          & \
                      (self.mRef660 > 0)          & \
                      (self.mRef870 > 0)          & \
                      (self.mRef1200 > 0)         & \
                      (self.mRef1600 > 0)         & \
                      (self.mRef2100 > 0)         & \
                      (self.mSre470 >  0.0)       & \
                      (self.mSre660>  0.0)        &\
                      (self.mSre2100 > 0.0)   

        DEEPiValid =  (dbl.qa==3)                & \
                      (dbl.aTau470 > -0.01)      & \
                      (dbl.aTau550 > -0.01)      & \
                      (dbl.aTau660 > -0.01)      & \
                      (dbl.mTau412 > -0.01)      & \
                      (dbl.mTau470 > -0.01)      & \
                      (dbl.mTau550 > -0.01)      & \
                      (dbl.mTau660 > -0.01)      & \
                      (dbl.cloud<cloud_thresh)   & \
                      (dbl.cloud > 0)           & \
                      (dbl.ScatteringAngle<170.) & \
                      (dbl.mRef412 > 0)          & \
                      (dbl.mRef440 > 0)          & \
                      (dbl.mRef470 > 0)          & \
                      (dbl.mRef550 > 0)          & \
                      (dbl.mRef660 > 0)          & \
                      (dbl.mRef870 > 0)          & \
                      (dbl.mRef1200 > 0)         & \
                      (dbl.mRef1600 > 0)         & \
                      (dbl.mRef2100 > 0)         & \
                      (dbl.mSre412 >  0.0)       & \
                      (dbl.mSre470 >  0.0)       & \
                      (dbl.mSre660>  0.0)       


        LANDref    =  (self.mRef412 > 0)          & \
                      (self.mRef440 > 0)          & \
                      (self.mRef470 > 0)          & \
                      (self.mRef550 > 0)          & \
                      (self.mRef660 > 0)          & \
                      (self.mRef870 > 0)          & \
                      (self.mRef1200 > 0)         & \
                      (self.mRef1600 > 0)         & \
                      (self.mRef2100 > 0)         & \
                      (self.mSre470 >  0.0)       & \
                      (self.mSre660>  0.0)        &\
                      (self.mSre2100 > 0.0)  
       
        addiValid = (LANDiValid == False) & (DEEPiValid) & (LANDref)

        if useDEEP:
          replace = ['mRef412','mRef470','mRef660','mSre470','mSre660','mTau550']          
        else:
          replace = ['mTau550']
        for name in replace:
          self.__dict__[name][addiValid] = dbl.__dict__[name][addiValid]

        self.iValid = LANDiValid
        self.iValid[addiValid] = True

        # Filter by additional variables
        # ------------------------------
        self.addFilter(aFilter)
        
        # Outlier removal based on log-transformed AOD
        # --------------------------------------------
        self.outlierRemoval(outliers)

        # Reduce the Dataset
        # --------------------
        self.reduce(self.iValid)                    
        self.iValid = ones(self.lon.shape).astype(bool)        

        # Angle transforms: for NN work we work with cosine of angles
        # -----------------------------------------------------------
        self.angleTranform()    

# ......................................................................
class QC_DBDT_INT (LAND,QC):

    def __init__ (self, fname,
                  useDEEP = False,
                  testDEEP= False,
                  Albedo=['MOD43BClimAlbedo'],
                  outliers=3.,
                  laod=True,
                  verbose=0,
                  cloud_thresh=0.70,
                  aFilter=None):
        """
        Initializes QC for the intersection of Land/Deep Blue points.

        On Input,

        fname   ---  file name for the CSV file with the co-located MODIS/AERONET
                     data (see class OCEAN)

        Albedo  ---  albedo file name identifier; albedo file will be created
                     from this identifier (See below).
        outliers --  number of standard deviations for outlinear removal.
        laod    ---  if True, targets are log-transformed AOD, log(Tau+0.01)
        """

        self.verbose = verbose
        self.laod = laod

        LAND.__init__(self,fname)  # initialize superclass
        dbl = DEEP(fname)

        # Get Auxiliary Data
        QC.__init__(self,fname,Albedo)        

        # Q/C: enforce QA=3 and scattering angle<170
        # Combines deep blue and dark target
        # -------------------------------------------
        LANDiValid =  (self.qa==3)                & \
                      (self.aTau470 > -0.01)      & \
                      (self.aTau550 > -0.01)      & \
                      (self.aTau660 > -0.01)      & \
                      (self.mTau470 > -0.01)      & \
                      (self.mTau550 > -0.01)      & \
                      (self.mTau660 > -0.01)      & \
                      (self.cloud<cloud_thresh)   & \
                      (self.cloud > 0)            & \
                      (self.ScatteringAngle<170.) & \
                      (self.mRef412 > 0)          & \
                      (self.mRef440 > 0)          & \
                      (self.mRef470 > 0)          & \
                      (self.mRef550 > 0)          & \
                      (self.mRef660 > 0)          & \
                      (self.mRef870 > 0)          & \
                      (self.mRef1200 > 0)         & \
                      (self.mRef1600 > 0)         & \
                      (self.mRef2100 > 0)         & \
                      (self.mSre470 >  0.0)       & \
                      (self.mSre660>  0.0)        &\
                      (self.mSre2100 > 0.0)  

        DEEPiValid =  (dbl.qa==3)                & \
                      (dbl.aTau470 > -0.01)      & \
                      (dbl.aTau550 > -0.01)      & \
                      (dbl.aTau660 > -0.01)      & \
                      (dbl.mTau412 > -0.01)      & \
                      (dbl.mTau470 > -0.01)      & \
                      (dbl.mTau550 > -0.01)      & \
                      (dbl.mTau660 > -0.01)      & \
                      (dbl.cloud<cloud_thresh)   & \
                      (dbl.cloud > 0)            & \
                      (dbl.ScatteringAngle<170.) & \
                      (dbl.mRef412 > 0)          & \
                      (dbl.mRef470 > 0)          & \
                      (dbl.mRef660 > 0)          & \
                      (dbl.mSre412 >  0.0)       & \
                      (dbl.mSre470 >  0.0)       & \
                      (dbl.mSre660>  0.0)       

        # Where both LAND and DEEP decide to retrieve
        intiValid = LANDiValid & DEEPiValid

        if useDEEP:
          replace = ['mRef412','mRef470','mRef660','mSre470','mSre660']
          add     = ['mSre412']
          for name in replace:
            self.__dict__[name][intiValid] = dbl.__dict__[name][intiValid]
          for name in add:
            self.__dict__[name] = dbl.__dict__[name]
            self.variables.append(name)  

        if testDEEP:
          replace = ['mTau550']
          for name in replace:
            self.__dict__[name][intiValid] = dbl.__dict__[name][intiValid]          

        self.iValid = intiValid

        self.dbmTau550 = dbl.mTau550
        self.variables.append('dbmTau550')  

        # Filter by additional variables
        # ------------------------------
        self.addFilter(aFilter)
        
        # Outlier removal based on log-transformed AOD
        # --------------------------------------------
        self.outlierRemoval(outliers)

        # Reduce the Dataset
        # --------------------
        self.reduce(self.iValid)                    
        self.iValid = ones(self.lon.shape).astype(bool)        

            
        # Angle transforms: for NN work we work with cosine of angles
        # -----------------------------------------------------------
        self.angleTranform()    

#----------------------------------------------------------------------------    

class QC_LAND_COMP (LAND,QC):

    def __init__ (self, fname,
                  useDEEP = False,
                  Albedo=['MOD43BClimAlbedo'],
                  outliers=3.,
                  laod=True,
                  verbose=0,
                  cloud_thresh=0.70,
                  aFilter=None):
        """
        Initializes QC for the complement of Dark Target + Deep Blue points.

        On Input,

        fname   ---  file name for the CSV file with the co-located MODIS/AERONET
                     data (see class OCEAN)

        Albedo  ---  albedo file name identifier; albedo file will be created
                     from this identifier (See below).
        outliers --  number of standard deviations for outlinear removal.
        laod    ---  if True, targets are log-transformed AOD, log(Tau+0.01)
        """

        self.verbose = verbose
        self.laod = laod

        LAND.__init__(self,fname)  # initialize superclass
        dbl = DEEP(fname)

        # Get Auxiliary Data
        QC.__init__(self,fname,Albedo)                

        # Q/C: enforce QA=3 and scattering angle<170
        # Combines deep blue and dark target
        # ------------------------------------------
        LANDiValid =  (self.qa==3)                & \
                      (self.aTau470 > -0.01)      & \
                      (self.aTau550 > -0.01)      & \
                      (self.aTau660 > -0.01)      & \
                      (self.mTau470 > -0.01)      & \
                      (self.mTau550 > -0.01)      & \
                      (self.mTau660 > -0.01)      & \
                      (self.cloud<cloud_thresh)   & \
                      (self.cloud > 0)            & \
                      (self.ScatteringAngle<170.) & \
                      (self.mRef412 > 0)          & \
                      (self.mRef440 > 0)          & \
                      (self.mRef470 > 0)          & \
                      (self.mRef550 > 0)          & \
                      (self.mRef660 > 0)          & \
                      (self.mRef870 > 0)          & \
                      (self.mRef1200 > 0)         & \
                      (self.mRef1600 > 0)         & \
                      (self.mRef2100 > 0)         & \
                      (self.mSre470 >  0.0)       & \
                      (self.mSre660>  0.0)        &\
                      (self.mSre2100 > 0.0)  

        DEEPiValid =  (dbl.qa==3)                & \
                      (dbl.aTau470 > -0.01)      & \
                      (dbl.aTau550 > -0.01)      & \
                      (dbl.aTau660 > -0.01)      & \
                      (dbl.mTau412 > -0.01)      & \
                      (dbl.mTau470 > -0.01)      & \
                      (dbl.mTau550 > -0.01)      & \
                      (dbl.mTau660 > -0.01)      & \
                      (dbl.cloud<cloud_thresh)   & \
                      (dbl.cloud > 0)           & \
                      (dbl.ScatteringAngle<170.) & \
                      (dbl.mRef412 > 0)          & \
                      (dbl.mRef470 > 0)          & \
                      (dbl.mRef660 > 0)          & \
                      (dbl.mSre412 >  0.0)       & \
                      (dbl.mSre470 >  0.0)       & \
                      (dbl.mSre660>  0.0)       

        DEEPref    =  (dbl.mRef412 > 0)          & \
                      (dbl.mRef470 > 0)          & \
                      (dbl.mRef660 > 0)          & \
                      (dbl.mSre412 >  0.0)       & \
                      (dbl.mSre470 >  0.0)       & \
                      (dbl.mSre660>  0.0)       

        # Where LAND retrieves, and DEEP does not
        # The LAND Complement
        compiValid = LANDiValid & ~DEEPiValid

        if useDEEP:
          compiValid = compiValid & DEEPref
          replace = ['mRef412','mRef470','mRef660','mSre470','mSre660']
          add     = ['mSre412']
          for name in replace:
            self.__dict__[name][compiValid] = dbl.__dict__[name][compiValid]
          for name in add:
            self.__dict__[name] = dbl.__dict__[name]
            self.variables.append(name)  

        self.iValid = compiValid


        # Filter by additional variables
        # ------------------------------
        self.addFilter(aFilter)
        
        # Outlier removal based on log-transformed AOD
        # --------------------------------------------
        self.outlierRemoval(outliers)

        # Reduce the Dataset
        # --------------------
        self.reduce(self.iValid)                    
        self.iValid = ones(self.lon.shape).astype(bool)        

            
        # Angle transforms: for NN work we work with cosine of angles
        # -----------------------------------------------------------
        self.angleTranform()



#..........................................
class QC_DEEP_COMP (DEEP,QC):

    def __init__ (self, fname,
                  useLAND = False,
                  DBDT=False,
                  noLANDref=False,
                  Albedo=['MOD43BClimAlbedo'],
                  outliers=3.,
                  laod=True,
                  verbose=0,
                  cloud_thresh=0.70,
                  aFilter=None):
        """
        Initializes the AOD Bias Correction (QC) for the MODIS Land algorithm.

        On Input,

        fname   ---  file name for the CSV file with the co-located MODIS/AERONET
                     data (see class OCEAN)

        Albedo  ---  albedo file name identifier; albedo file will be created
                     from this identifier (See below).
        outliers --  number of standard deviations for outlinear removal.
        laod    ---  if True, targets are log-transformed AOD, log(Tau+0.01)
        """

        self.verbose = verbose
        self.laod = laod

        DEEP.__init__(self,fname)  # initialize superclass
        lnd = LAND(fname)

        # Get Auxiliary Data
        QC.__init__(self,fname,Albedo)           


        # Q/C: enforce QA=3 and scattering angle<170
        # Combines deep blue and dark target
        # --------------------------------------------------------------
        LANDiValid =  (lnd.qa==3)                & \
                      (lnd.aTau470 > -0.01)      & \
                      (lnd.aTau550 > -0.01)      & \
                      (lnd.aTau660 > -0.01)      & \
                      (lnd.mTau470 > -0.01)      & \
                      (lnd.mTau550 > -0.01)      & \
                      (lnd.mTau660 > -0.01)      & \
                      (lnd.cloud<cloud_thresh)   & \
                      (lnd.cloud > 0)            & \
                      (lnd.ScatteringAngle<170.) & \
                      (lnd.mRef412 > 0)          & \
                      (lnd.mRef440 > 0)          & \
                      (lnd.mRef470 > 0)          & \
                      (lnd.mRef550 > 0)          & \
                      (lnd.mRef660 > 0)          & \
                      (lnd.mRef870 > 0)          & \
                      (lnd.mRef1200 > 0)         & \
                      (lnd.mRef1600 > 0)         & \
                      (lnd.mRef2100 > 0)         & \
                      (lnd.mSre470 >  0.0)       & \
                      (lnd.mSre660>  0.0)        &\
                      (lnd.mSre2100 > 0.0)  

        DEEPiValid =  (self.qa==3)                & \
                      (self.aTau470 > -0.01)      & \
                      (self.aTau550 > -0.01)      & \
                      (self.aTau660 > -0.01)      & \
                      (self.mTau412 > -0.01)      & \
                      (self.mTau470 > -0.01)      & \
                      (self.mTau550 > -0.01)      & \
                      (self.mTau660 > -0.01)      & \
                      (self.cloud<cloud_thresh)   & \
                      (self.cloud > 0)           & \
                      (self.ScatteringAngle<170.) & \
                      (self.mRef412 > 0)          & \
                      (self.mRef470 > 0)          & \
                      (self.mRef660 > 0)          & \
                      (self.mSre412 >  0.0)       & \
                      (self.mSre470 >  0.0)       & \
                      (self.mSre660>  0.0)       

        LANDref    =  (lnd.mRef412 > 0)          & \
                      (lnd.mRef440 > 0)          & \
                      (lnd.mRef470 > 0)          & \
                      (lnd.mRef550 > 0)          & \
                      (lnd.mRef660 > 0)          & \
                      (lnd.mRef870 > 0)          & \
                      (lnd.mRef1200 > 0)         & \
                      (lnd.mRef1600 > 0)         & \
                      (lnd.mRef2100 > 0)         & \
                      (lnd.mSre470 >  0.0)       & \
                      (lnd.mSre660>  0.0)        &\
                      (lnd.mSre2100 > 0.0)  

        # Where DEEP retrieves, and LAND does not
        # The DEEP Complement
        compiValid = ~LANDiValid & DEEPiValid

        if useLAND:
          compiValid = compiValid & LANDref
          replace = ['mRef412','mRef440','mRef470','mRef550','mRef660','mRef870',
                     'mRef1200','mRef1600','mRef2100','mSre470','mSre660']
          add     = ['mSre2100']

          for name in add:
            self.__dict__[name] = lnd.__dict__[name]
            self.variables.append(name)  
          if not DBDT:
            for name in replace:
              self.__dict__[name][compiValid] = lnd.__dict__[name][compiValid]
        elif noLANDref:
          compiValid = compiValid & ~LANDref


        self.iValid = compiValid

        # Filter by additional variables
        # ------------------------------
        self.addFilter(aFilter)
        
        # Outlier removal based on log-transformed AOD
        # --------------------------------------------
        self.outlierRemoval(outliers)

        # Reduce the Dataset
        # --------------------
        self.reduce(self.iValid)                    
        self.iValid = ones(self.lon.shape).astype(bool)        

            
        # Angle transforms: for NN work we work with cosine of angles
        # -----------------------------------------------------------
        self.angleTranform()    


#-------------------------------------------------------------------------------
  
if __name__ == "__main__":

  """
    Examples.
  """

  sat = 'Aqua' # 'Terra'

  if sat == 'Terra':
    filename     = './data/giant_C6_10km_Terra_20150921.nc'
  elif sat == 'Aqua':
    filename     = './data/giant_C6_10km_Aqua_20151005.nc'
  
  #                             ---------------
  #                             Ocean Algorithm
  #                             ---------------
  
  Albedo = ['CoxMunkBRF']


  # Ocean Model
  # -----------
  Angles = ['SolarZenith','ScatteringAngle', 'GlintAngle']
  Reflectances = [ 'mRef470',
                   'mRef550',
                   'mRef660',
                   'mRef870',
                   'mRef1200',
                   'mRef1600',
                   'mRef2100']
  
  Surface = [ 'CxAlbedo470',
              'CxAlbedo550',
              'CxAlbedo660',
              'CxAlbedo870',
              'CxAlbedo1200',
              'CxAlbedo1600',
              'CxAlbedo2100' ]
  
  Species = [ 'fdu','fcc','fsu']

  Features = Angles + Reflectances + Surface + Species
  Target = ['aTau470','aTau550','aTau660','aTau870']


  # Ingest Quality Controled Data
  # -----------------------------
  Albedo = ['CxAlbedo']
  aFilter = Surface # additional filter
  ocean = QC_OCEAN(filename,Albedo=Albedo,verbose=True,aFilter=aFilter)


  

