"""
   This module implements a Neural Net based MODIS Collection 6 Neural Net Retrieval.

   Arlindo da Silva, June 2015.

"""

import os, sys
import numpy                as      np
from   .giant_viirs          import  MISSING, DT_LAND, DT_OCEAN, DB_LAND, DB_OCEAN, DB_DEEP
from   .nn                   import  NN
import itertools
from   sklearn.preprocessing import StandardScaler
from   multiprocessing      import cpu_count
from   .abc_c6_aux          import TestStats
from   .brdf                import rtlsReflectance
from   .mcd43c              import BRDF
from   functools            import reduce
from   glob                 import glob
from   .evaluation          import EVAL
# ------

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
class SETUP(object):
    def __init__(self):
        pass
    def setupNN(self,retrieval,expid,
                 nHidden=None,
                 nHLayers=1,
                 combinations=False,
                 Input_nnr  = ['mRef470','mRef550','mRef660', 'mRef870',
                                'mRef1200','mRef1600','mRef2100',
                                'ScatteringAngle', 'GlintAngle',
                                'AMF', 'SolarZenith',
                                'cloud', 'albedo','fdu','fcc','fsu' ],
                 Input_const = None,
                 Target = ['aTau550',],
                 K=None,
                 f_balance=0.50,
                 q_balance=True,
                 q_balance_enhance=False,
                 minN=500,
                 fignore=[],
                 nbins = 6,
                 lInput_nnr = None):

        """
        lInput_nnr --- optional, give a list of the nnr input variables that you want to log transform
        """  
    
        self.retrieval = retrieval
        self.lInput_nnr = lInput_nnr
        # Create outdir if it doesn't exist
        # ---------------------------------
        self.outdir = "./{}/".format(expid)
        if not os.path.exists(self.outdir):
            os.makedirs(self.outdir)

        self.plotdir = self.outdir

        # save some inputs
        # -----------------
        self.expid   = expid
        self.Target  = Target
        self.nTarget = len(Target)
        self.K       = K
        self.nHidden = nHidden

        # figure out if you need to calculate 
        # the angstrom exponent at each wavelength
        # of the angstrom fit for all wavelengths
        # ---------------------------------------
        angstrom = False
        angstrom_fit = False
        for tname in Target:
            if not angstrom:
                if ('AE' in tname) and ('AEfit' not in tname):
                    angstrom = True
                if not angstrom_fit:
                    if 'AEfit' in tname:
                        angstrom_fit = True
        self.angstrom = angstrom
        self.angstrom_fit = angstrom_fit

        # if angstrom is being trained
        # find the base wavelength
        # calculate angstrom with respect to the base wavelength
        # -----------------------------------------------------
        if angstrom:
            self.get_aAE()
            self.get_mAE()

        # if angstrom_fit is being trained
        # calculate a linear fit to the log-log
        # of wavelength and AOD 440-870
        # -------------------------------------------------------
        if angstrom_fit:
            self.get_aAEfit()
            self.get_mAEfit()

        # Fit the standard scalar of the targets
        # ---------------------------------------
        self.scaler = None
        if self.scale:
            targets = self.getTargets(self.iValid) 
            self.scaler = StandardScaler()
            if self.nTarget == 1:
                self.scaler.fit(targets.reshape(-1,1))
            else:
                self.scaler.fit(targets)

        # Balance the dataset before splitting
        # No aerosol type should make up more that 35% 
        # of the total number of obs
        # f_balance is the fraction that defines whether a species 'dominates'
        # --------------------------------------
        self.f_balance = f_balance
        self.q_balance = q_balance
        self.q_balance_enhance = q_balance_enhance
        if q_balance:
            self.minN = minN
            self.fignore = fignore
            self.iValid = self.spc_target_balance(minN=minN,frac=f_balance,fignore=fignore,nbins=nbins)
        elif q_balance_enhance:
            self.fignore = fignore
            np.random.seed(32768)  # so that we get the same permutation
            P = np.random.permutation(self.nobs)
            k = np.arange(self.nobs)
            self.iTest = np.zeros([self.nobs]).astype(bool)
            self.iTrain = np.ones([self.nobs]).astype(bool)
            self.iTest[k[P[0:int(self.nobs*0.3)]]] = True
            self.iTrain[k[P[0:int(self.nobs*0.3)]]] = False

            self.spc_target_balance(frac=f_balance,fignore=fignore,nbins=nbins)
            nadd = self.nobs - len(k)
            self.iTest = np.append(self.iTest,np.zeros(nadd).astype(bool))
            self.iTrain = np.append(self.iTrain,np.ones(nadd).astype(bool))
            
        elif f_balance > 0:
#            self.iValid = self.spc_balance(int(self.nobs*0.35),frac=f_balance)
            self.iValid = self.balance(int(self.nobs*0.35),frac=f_balance)

        # Flatten Input_nnr into one list
        # -------------------------------
        input_nnr = flatten_list(Input_nnr)

        # Create list of combinations
        # ---------------------------
        if combinations:
            self.comblist, self.combgroups = get_combinations(Input_nnr,Input_const)
        else:
            self.comblist = [input_nnr]
              
        # Initialize arrays to hold stats
        # ------------------------------
        self.nnr  = STATS(K,self.comblist,self.nTarget)
        self.orig = STATS(K,self.comblist,self.nTarget)

        # Initialize K-folding
        # --------------------
        if K is None:
            if not self.q_balance_enhance:
                self.iTest = np.ones([self.nobs]).astype(bool)
                self.iTrain = np.ones([self.nobs]).astype(bool)
                if (f_balance > 0) or q_balance:
                    self.iTest = ~self.iValid.copy()
                    self.iTrain = self.iValid.copy()
        else:
            self.kfold(K=K)

        # Create list of topologies
        # -------------------------  
        self.topology = []
        if not combinations:
            if self.nHidden is None:
                self.nHidden  = len(input_nnr)
            else:
                self.nHidden = nHidden

            self.topology.append((len(input_nnr),) + (self.nHidden,)*nHLayers + (len(Target),))

        else:
            for c,Input in enumerate(self.comblist):
                if nHidden is None:
                    self.nHidden  = len(Input)
                else:
                    self.nHidden = nHidden

                self.topology.append((len(Input),) + (self.nHidden,)*nHLayers + (len(Target),))

        self.combinations = combinations


        # optional log transform input variables log
        if lInput_nnr is not None:
            for vname in lInput_nnr:
#                self.__dict__['l'+vname] = np.log(self.__dict__[vname]+0.01)
                self.__dict__['scaler_l'+vname] = StandardScaler()
                feature = self.__dict__[vname]
                self.__dict__['scaler_l'+vname].fit(feature.reshape(-1,1))
                self.__dict__['l'+vname] = self.__dict__['scaler_l'+vname].transform(feature.reshape(-1,1)).squeeze()


# ---
    def get_aAE(self):
        """ 
        if angstrom is being trained
        find the base wavelength
        """
        # find base wavelength
        for i,tname in enumerate(self.Target):
            if 'Tau' in tname:
                base_name = tname
                base_wavs = tname.split('Tau')[-1]
                base_wav = float(base_wavs)
                base_tau = self.__dict__[tname]
                base_wav_i = i

        self.AE_base_wav = base_wav
        self.AE_base_wav_i = base_wav_i
    
        # Calculate the angstrom exponent
        # with respect to the base wavelength
        for tname in self.Target:
            if 'Tau' not in tname:
                wavs = tname.split('AE')[-1]
                wav  = float(wavs)
                tau  = self.__dict__['aTau'+wavs]
                AE = -1.*np.log(tau/base_tau)/np.log(wav/base_wav)
                self.__dict__['aAE'+wavs] = AE       
# ---
    def get_mAE(self):
        """
        get the AE from original retrieval
        """
        base_wav = self.AE_base_wav
        base_wav_i = self.AE_base_wav_i 

        # Calculate the angstrom exponent
        # with respect to the base wavelength
        for tname in self.Target:
            if 'Tau' not in tname:
                wavs = tname.split('AE')[-1]
                wav  = float(wavs)
                if 'mTau'+wavs in self.__dict__:
                    tau  = self.__dict__['mTau'+wavs]
                    AE = -1.*np.log(tau/base_tau)/np.log(wav/base_wav)
                    self.__dict__['mAE'+wavs] = AE                
# ---
    def get_aAEfit(self):
        """
        calculate a linear fit to the log-log
        of wavelength and AOD 440-870        
        """

        wavs = ['440','470','500','550','660','870']
        wav  = np.array(wavs).astype(float)

        # Calculate the angstrom exponent
        # with a linear fit to log AOD
        tau = []
        for w in wavs:
            tau.append(self.__dict__['aTau'+w])

        tau = np.array(tau)
        fit = np.polyfit(np.log(wav),-1.*np.log(tau+0.01),1)
        self.__dict__['aAEfitm'] = fit[0,:]
        self.__dict__['aAEfitb'] = fit[1,:]      
        self.wavs = wavs

# ---
    def get_mAEfit(self):
        """
        calculate a linear fit to the log-log
        of wavelength and AOD 440-870 
        for the original retrieval data
        """
        wavs = self.wavs

        # Calculate the angstrom exponent
        # with a linear fit to log AOD
        tau = []
        wav = []
        for w in wavs:
            if 'mTau'+w in self.__dict__:
                tau.append(self.__dict__['mTau'+w])
                wav.append(float(w))

        tau = np.array(tau)
        wav = np.array(wav)
        fit = np.polyfit(np.log(wav),-1.*np.log(tau+0.01),1)
        self.__dict__['mAEfitm'] = fit[0,:]
        self.__dict__['mAEfitb'] = fit[1,:]

#----------------------------------------------------------------------------    
class ABC(object):

    """
    Common Subroutines to all the ABC Classes
    """

    def __init__(self,fname,Albedo,coxmunk_lut=None,NDVI=False,aerFile=None,slvFile=None):

        # Get Auxiliary Data
        if type(fname) is str:
            self.fnameRoot = fname[:-3]
        else:
           self.fnameRoot = [fname[:-3]]

        self.aerFile = aerFile
        self.slvFile = slvFile        
        self.setWind()
        self.setAlbedo(Albedo,coxmunk_lut=coxmunk_lut)
        self.setSpec()
        if NDVI:
            self.setNDVI()

    def setWind(self):
        # Read in wind
        # ------------------------
        if self.aerFile is None:
            self.aerFile = sorted(glob(self.fnameRoot + "_MERRA2*.npz"))
        first = True
        for filename in self.aerFile:
            if 'wind' in np.load(filename).keys():
                data = np.load(filename)['wind']
            else:
                data = np.sqrt(np.load(filename)['u10m']**2 + np.load(filename)['v10m']**2)
            if first:
                self.wind = data
            else:
                self.wind = np.append(self.wind,data)
            first = False
        self.giantList.append('wind')
        self.Wind = '' #need this for backwards compatibility
        if self.Ityme is not None:
            self.wind = self.wind[self.Ityme]        

    def setAlbedo(self,Albedo,coxmunk_lut=None):
        # Define wind speed dependent ocean albedo
        # ----------------------------------------
        if Albedo is not None:
          for albedo in Albedo:
            if albedo == 'CoxMunkLUT':
              self.getCoxMunk(coxmunk_lut) 
              self.giantList.append(albedo)    
            elif albedo == 'MCD43C1':
              self.setBRDF()     
            elif 'CxAlbedo' in albedo :
              self.setCoxMunkBRF(albedo)
            else:
              self.__dict__[albedo] = np.squeeze(np.load(self.fnameRoot+'_'+albedo+'.npz')["albedo"])
              self.giantList.append(albedo)

    def setSpec(self):
        # Read in Aerosol Fractional Composition
        # --------------------------------------
        names = ('fdu','fss','fcc','fsu','fni')
        for name in names:
            if self.aerFile is None:
                self.aerFile = sorted(glob(self.fnameRoot + "_MERRA2*.npz"))
            first = True
            for filename in self.aerFile:
                try:
                    data = np.load(filename)[name]
                    if first:
                        self.__dict__[name] = data
                        self.giantList.append(name)
                    else:
                        self.__dict__[name] = np.append(self.__dict__[name],data)
                except:
                    print('+++++++ '+name + ' not found in '+ filename)
                first = False

            if self.Ityme is not None:
                self.__dict__[name] = self.__dict__[name][self.Ityme]


    def setCoxMunkBRF(self,albedo):
        # Read in Cox Munk Bidirectional surface reflectance
        # --------------------------------------------------
        names = ['470','550','660','870','1200','1600','2100']
        for ch in names:
            name = 'CxAlbedo' + ch
            self.__dict__[name] = np.squeeze(np.load(self.fnameRoot+'_CxAlbedo.npz')[name])
            self.giantList.append(name)

    def setBRDF(self):
        # Read in MCD43C1 BRDF
        # Calculate bidirectional surface reflectance
        # ---------------------------------------------
        brdf = BRDF(self.nobs)
        names = ('BRDFvis','BRDFnir','BRDF470','BRDF550',
                 'BRDF650','BRDF850','BRDF1200','BRDF1600',
                 'BRDF2100')
        for name in brdf.__dict__:
            brdf.__dict__[name] = np.load(self.fnameRoot + "_MCD43C1.npz")[name]

        for name in names:
            ch = name[4:]
            Kiso = brdf.__dict__['Riso'+ch]
            Kvol = brdf.__dict__['Rvol'+ch]
            Kgeo = brdf.__dict__['Rgeo'+ch]
            self.__dict__[name] = rtlsReflectance(Kiso,Kgeo,Kvol,
                                                  self.SolarZenith,self.SensorZenith,
                                                  None,None,
                                                  raa=self.RelativeAzimuth)
            self.giantList.append(name)    


    def setNDVI(self):
        # Read in NDVI
        # -------------
        names = ('NDVI','EVI','NIRref')
        for name in names:
          self.__dict__[name] = np.load(self.fnameRoot + "_NDVI.npz")[name]
          self.giantList.append(name)

    def outlierRemoval(self,outliers):

        # # Outlier removal based on log-transformed AOD
        # # --------------------------------------------
        if outliers > 0.:
            d = np.log(self.mTau550[self.iValid]+self.logoffset) - np.log(self.aTau550[self.iValid]+self.logoffset)
            if self.verbose>0:
                print("Outlier removal: %d   sig_d = %f  nGood=%d "%(-1,np.std(d),d.size))
            for iter in range(3):
                iValid = (abs(d)<outliers*np.std(d))
                self.iValid[self.iValid] = iValid
                d = np.log(self.mTau550[self.iValid]+self.logoffset) - np.log(self.aTau550[self.iValid]+self.logoffset)
                if self.verbose>0:
                    print("Outlier removal: %d   sig_d = %f  nGood=%d "%(iter,np.std(d),d.size))
              
    def angleTranform(self):            
        # Angle transforms: for NN work we work with cosine of angles
        # -----------------------------------------------------------
        self.ScatteringAngle = np.cos(self.ScatteringAngle*np.pi/180.0) 
        self.SensorZenith    = np.cos(self.SensorZenith*np.pi/180.0)    
        self.SolarZenith     = np.cos(self.SolarZenith*np.pi/180.0)     
        self.GlintAngle      = np.cos(self.GlintAngle*np.pi/180.0)      
        self.AMF             = (1/self.SolarZenith) + (1/self.SensorZenith)
        self.giantList.append('AMF')

    def setYear(self):
        # Year
        #-------
        self.year = np.array([t.year for t in self.tyme])
        self.giantList.append('year')

    def addFilter(self,aFilter):
        if aFilter is not None:
          filters = []
          for f in aFilter:
            filters.append(self.__dict__[f]>0)
            
          oiValid = reduce(lambda x,y: x&y,filters)
          self.iValid = self.iValid & oiValid

#---------------------------------------------------------------------------- 
class ABC_DT_Ocean (DT_OCEAN,NN,SETUP,ABC):

    def __init__ (self,fname, 
                  coxmunk_lut='/nobackup/NNR/Misc/coxmunk_lut.npz',
                  outliers=3., 
                  laod=True,
                  logoffset=0.01,
                  verbose=0,
                  cloud_thresh=0.70,
                  glint_thresh=40.0,
                  Albedo=None,
                  aFilter=None,
                  tymemax=None,
                  aerFile=None,
                  slvFile=None):
        """
        Initializes the AOD Bias Correction (ABC) for the VIIRS DT Ocean algorithm.

        On Input,

        fname   ---  file name for the CSV file with the co-located MODIS/AERONET
                     data (see class OCEAN)
        outliers --  number of standard deviations for outlinear removal.
        laod    ---  if True, targets are log-transformed AOD, log(Tau+logoffset)
        logoffset -- offset to protect against taking log of 0 or negative
        tymemax ---  truncate the data record in the giant file at tymemax.
                     set to  None to read entire data record.


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
        self.logoffset = logoffset

        DT_OCEAN.__init__(self,fname,tymemax=tymemax) # initialize superclass

        # Get Auxiliary Data
        ABC.__init__(self,fname,Albedo,coxmunk_lut=coxmunk_lut,aerFile=aerFile,slvFile=slvFile)

        # Q/C
        # ---
        self.iValid = (self.qa>0) & \
                      (self.aTau470 > -0.01) &\
                      (self.aTau550 > -0.01) &\
                      (self.aTau660 > -0.01) &\
                      (self.aTau870 > -0.01) &\
                      (self.mTau480 > -0.01) &\
                      (self.mTau550 > -0.01) &\
                      (self.mTau670 > -0.01) &\
                      (self.mTau860 > -0.01) &\
                      (self.mRef480 > 0.0)   &\
                      (self.mRef550 > 0.0)   &\
                      (self.mRef670 > 0.0)   &\
                      (self.mRef860 > 0.0)   &\
                      (self.mRef1240 > 0.0)  &\
                      (self.mRef1600 > 0.0)  &\
                      (self.mRef2250 > 0.0)  &\
                      (self.cloud <cloud_thresh) &\
                      (self.cloud >= 0)          &\
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
        self.iValid = np.ones(self.lon.shape).astype(bool)
            
        # Angle transforms: for NN work we work with cosine of angles
        # -----------------------------------------------------------
        self.angleTranform()

        # Year
        #-------
        self.setYear()

#----------------------------------------------------------------------------
class ABC_DB_Ocean (DB_OCEAN,NN,SETUP,ABC,EVAL):

    def __init__ (self,fname,
                  coxmunk_lut='/nobackup/NNR/Misc/coxmunk_lut.npz',
                  outliers=3.,
                  laod=True,
                  scale=False,
                  logoffset=0.01,
                  verbose=0,
                  cloud_thresh=0.70,
                  glint_thresh=40.0,
                  Albedo=None,
                  aFilter=None,
                  tymemax=None,
                  aerFile=None,
                  slvFile=None):
        """
        Initializes the AOD Bias Correction (ABC) for the VIIRS DB Ocean algorithm.

        On Input,

        fname   ---  file name for the CSV file with the co-located MODIS/AERONET
                     data (see class OCEAN)
        outliers --  number of standard deviations for outlinear removal.
        laod    ---  if True, targets are log-transformed AOD, log(Tau+logoffset)
        logoffset -- offset to protect against taking log of 0 or negative
        tymemax ---  truncate the data record in the giant file at tymemax.
                     set to  None to read entire data record.


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
        self.scale   = scale
        self.logoffset = logoffset

        DB_OCEAN.__init__(self,fname,tymemax=tymemax) # initialize superclass

        # Get Auxiliary Data
        ABC.__init__(self,fname,Albedo,coxmunk_lut=coxmunk_lut,aerFile=aerFile,slvFile=slvFile)

        # Q/C
        # algflag filter keeps only non-turbid pixels
        # ---
        self.iValid = (self.qa>0) & \
                      (self.algflag == 0) &\
                      (self.aTau470 > -0.01) &\
                      (self.aTau550 > -0.01) &\
                      (self.aTau660 > -0.01) &\
                      (self.aTau870 > -0.01) &\
                      (self.mTau488 > -0.01) &\
                      (self.mTau550 > -0.01) &\
                      (self.mTau670 > -0.01) &\
                      (self.mTau865 > -0.01) &\
                      (self.mTau1240 > -0.01) &\
                      (self.mTau1640 > -0.01) &\
                      (self.mTau2250 > -0.01) &\
                      (self.mRef412 > 0.0)   &\
                      (self.mRef488 > 0.0)   &\
                      (self.mRef550 > 0.0)   &\
                      (self.mRef670 > 0.0)   &\
                      (self.mRef865 > 0.0)   &\
                      (self.mRef1240 > 0.0)  &\
                      (self.mRef1640 > 0.0)  &\
                      (self.mRef2250 > 0.0)  &\
                      (self.cloud <cloud_thresh) &\
                      (self.cloud >= 0)          &\
                      (self.GlintAngle != MISSING ) &\
                      (self.GlintAngle > glint_thresh)

        # Filter by additional variables
        # ------------------------------
        self.addFilter(aFilter)

        # glint_thresh > 40 is a bit redundant b/c MOD04 should already give these a qa==0 or
        # does not retrieve.  However, there are a few cases (~200) where this does not happen.
        # the GlingAngle is very close to 40, greater than 38.  Not sure why these get through.

        # Reduce the Dataset
        # --------------------
        self.reduce(self.iValid)
        self.iValid = np.ones(self.lon.shape).astype(bool)

        # Outlier removal based on log-transformed AOD
        # --------------------------------------------
        if outliers > 0 :
            self.outlierRemoval(outliers)       
            # save the indeces to be used for testing on the outliers later
            self.outValid = np.arange(self.nobs)[self.iValid]

            # Reduce the Dataset
            # --------------------
            self.reduce(self.iValid)
            self.iValid = np.ones(self.lon.shape).astype(bool)
            
        # Angle transforms: for NN work we work with cosine of angles
        # -----------------------------------------------------------
        self.angleTranform()

        # Year
        #-------
        self.setYear()
#----------------------------------------------------------------------------    

class ABC_DT_Land (DT_LAND,NN,SETUP,ABC,EVAL):

    def __init__ (self, fname,
                  Albedo=None,
                  alb_max = 0.25,
                  outliers=3.,
                  laod=True,
                  scale=False,
                  logoffset=0.01,
                  verbose=0,
                  cloud_thresh=0.70,
                  aFilter=None,
                  NDVI=False,
                  tymemax=None,
                  aerFile=None,
                  slvFile=None):
        """
        Initializes the AOD Bias Correction (ABC) for the VIIRS DT Land algorithm.

        On Input,

        fname   ---  file name for the CSV file with the co-located VIIRS/AERONET
                     data (see class OCEAN)

        Albedo  ---  albedo file name identifier; albedo file will be created
                     from this identifier (See below).
        outliers --  number of standard deviations for outlinear removal.
        laod    ---  if True, targets are log-transformed AOD, log(Tau+logoffset)
        logoffset -- offset to protect against taking log of 0 or negative
        tymemax ---  truncate the data record in the giant file at tymemax. 
                     set to  None to read entire data record.
        """

        self.verbose = verbose
        self.laod = laod
        self.logoffset = logoffset
        self.scale = self.scale

        DT_LAND.__init__(self,fname,tymemax=tymemax)  # initialize superclass

        # Get Auxiliary Data
        ABC.__init__(self,fname,Albedo,NDVI=NDVI,aerFile=aerFile,slvFile=slvFile)

        # Q/C: enforce QA=3 and albedo in (0,0.25), scattering angle<170
        # --------------------------------------------------------------
        self.iValid = (self.qa==3)                & \
                      (self.aTau470 > -0.01)      & \
                      (self.aTau550 > -0.01)      & \
                      (self.aTau660 > -0.01)      & \
                      (self.mTau480 > -0.01)      & \
                      (self.mTau550 > -0.01)      & \
                      (self.mTau670 > -0.01)      & \
                      (self.mTau2250> -0.01)      & \
                      (self.cloud<cloud_thresh)   & \
                      (self.cloud >= 0)           & \
                      (self.ScatteringAngle<170.) & \
                      (self.mRef480 > 0)          & \
                      (self.mRef670 > 0)          & \
                      (self.mRef2250 > 0)         & \
                      (self.mSre480 >  0.0)       & \
                      (self.mSre670 >  0.0)       & \
                      (self.mSre2250>  0.0)       

#                      (self.mRef412 > 0)          & \
#                      (self.mRef440 > 0)          & \
#                      (self.mRef550 > 0)          & \
#                      (self.mRef870 > 0)          & \
#                      (self.mRef1200 > 0)         & \
#                      (self.mRef1600 > 0)         & \

        # Filter by additional variables
        # ------------------------------
        self.addFilter(aFilter)

        
        # Outlier removal based on log-transformed AOD
        # --------------------------------------------
        self.outlierRemoval(outliers)

        # Reduce the Dataset
        # --------------------
        self.reduce(self.iValid)                    
        self.iValid = np.ones(self.lon.shape).astype(bool)        

        # Angle transforms: for NN work we work with cosine of angles
        # -----------------------------------------------------------
        self.angleTranform()   

#----------------------------------------------------------------------------

class ABC_DB_Deep (DB_DEEP,NN,SETUP,ABC,EVAL):

    def __init__ (self, fname,
                  Albedo=None,
                  outliers=3.,
                  laod=True,
                  scale=False,
                  logoffset=0.01,
                  verbose=0,
                  cloud_thresh=0.70,
                  aFilter=None,
                  NDVI=False,
                  tymemax=None,
                  algflag=None,
                  aerFile=None,
                  slvFile=None):
        """
        Initializes the AOD Bias Correction (ABC) for the MODIS Land algorithm.

        On Input,

        fname   ---  file name for the CSV file with the co-located MODIS/AERONET
                     data (see class OCEAN)

        Albedo  ---  albedo file name identifier; albedo file will be created
                     from this identifier (See below).
        outliers --  number of standard deviations for outlinear removal.
        laod    ---  if True, targets are log-transformed AOD, log(Tau+logoffset)
        logoffset -- offset to protect against taking log of 0 or negative
        tymemax ---  truncate the data record in the giant file at tymemax.
                     set to  None to read entire data record.
        algflag ---  DB Land algorithm flag number - this should be a list. Allows for selecting multiple algorithms.
                     None - don't filter, use all pixels
                     0 - hybrid (heterogenous surface)
                     1 - vegetated surface
                     2 - bright surface
                     3 - mixed
        """

        self.verbose = verbose
        self.laod = laod
        self.logoffset = logoffset
        self.algflag = algflag
        self.scale = scale

        DB_DEEP.__init__(self,fname,tymemax=tymemax)  # initialize superclass

        # Get Auxiliary Data
        ABC.__init__(self,fname,Albedo,NDVI=NDVI,aerFile=aerFile,slvFile=slvFile)

        # Q/C: enforce QA=3, scattering angle<170
        # --------------------------------------------------------------
        self.iValid = (self.qa==3)                & \
                      (self.aTau470 > -0.01)      & \
                      (self.aTau550 > -0.01)      & \
                      (self.aTau660 > -0.01)      & \
                      (self.mTau412 > -0.01)      & \
                      (self.mTau488 > -0.01)      & \
                      (self.mTau550 > -0.01)      & \
                      (self.mTau670 > -0.01)      & \
                      (self.cloud<cloud_thresh)   & \
                      (self.cloud >= 0)           & \
                      (self.ScatteringAngle<170.) & \
                      (self.mRef412 > 0)          & \
                      (self.mRef488 > 0)          & \
                      (self.mRef550 > 0)          & \
                      (self.mRef670 > 0)          & \
                      (self.mRef865 > 0)          & \
                      (self.mRef1240 > 0)         & \
                      (self.mRef1640 > 0)         & \
                      (self.mRef2250 > 0)         & \
                      (self.mSre488 >  0.0)       & \
                      (self.mSre670 >  0.0)       & \
                      (self.mSre412 >  0.0)

        if algflag is not None:
            fValid = np.zeros(self.iValid.shape).astype(bool)
            for aflag in algflag:
                fValid = fValid | (self.algflag == aflag)
            self.iValid = self.iValid & fValid


        # Filter by additional variables
        # ------------------------------
        self.addFilter(aFilter)

        # Reduce the Dataset
        # --------------------
        self.reduce(self.iValid)
        self.iValid = np.ones(self.lon.shape).astype(bool)

        # Outlier removal based on log-transformed AOD
        # --------------------------------------------
        if outliers > 0 :
            self.outlierRemoval(outliers)
            # save the indeces to be used for testing on the outliers later
            self.outValid = np.arange(self.nobs)[self.iValid]

            # Reduce the Dataset
            # --------------------
            self.reduce(self.iValid)
            self.iValid = np.ones(self.lon.shape).astype(bool)



        # Angle transforms: for NN work we work with cosine of angles
        # -----------------------------------------------------------
        self.angleTranform()

#----------------------------------------------------------------------------    

class ABC_DB_Land (DB_LAND,NN,SETUP,ABC,EVAL):

    def __init__ (self, fname,
                  Albedo=None,
                  outliers=3.,
                  laod=True,
                  scale=False,
                  logoffset=0.01,
                  verbose=0,
                  cloud_thresh=0.70,
                  aFilter=None,
                  NDVI=False,
                  tymemax=None,
                  algflag=None,
                  aerFile=None,
                  slvFile=None):
        """
        Initializes the AOD Bias Correction (ABC) for the MODIS Land algorithm.

        On Input,

        fname   ---  file name for the CSV file with the co-located MODIS/AERONET
                     data (see class OCEAN)

        Albedo  ---  albedo file name identifier; albedo file will be created
                     from this identifier (See below).
        outliers --  number of standard deviations for outlinear removal.
        laod    ---  if True, targets are log-transformed AOD, log(Tau+logoffset)
        logoffset -- offset to protect against taking log of 0 or negative 
        tymemax ---  truncate the data record in the giant file at tymemax.
                     set to  None to read entire data record.
        algflag ---  DB Land algorithm flag number - this should be a list. Allows for selecting multiple algorithms.
                     None - don't filter, use all pixels
                     0 - hybrid (heterogenous surface)
                     1 - vegetated surface
                     2 - bright surface
                     3 - mixed
        """

        self.verbose = verbose
        self.laod = laod
        self.scale = scale
        self.logoffset = logoffset
        self.algflag = algflag

        DB_LAND.__init__(self,fname,tymemax=tymemax)  # initialize superclass

        # Get Auxiliary Data
        ABC.__init__(self,fname,Albedo,NDVI=NDVI,aerFile=aerFile,slvFile=slvFile)

        # Q/C: enforce QA=3, scattering angle<170
        # --------------------------------------------------------------
        self.iValid = (self.qa==3)                & \
                      (self.aTau470 > -0.01)      & \
                      (self.aTau550 > -0.01)      & \
                      (self.aTau660 > -0.01)      & \
                      (self.mTau412 > -0.01)      & \
                      (self.mTau488 > -0.01)      & \
                      (self.mTau550 > -0.01)      & \
                      (self.mTau670 > -0.01)      & \
                      (self.cloud<cloud_thresh)   & \
                      (self.cloud >= 0)           & \
                      (self.ScatteringAngle<170.) & \
                      (self.mRef412 > 0)          & \
                      (self.mRef488 > 0)          & \
                      (self.mRef550 > 0)          & \
                      (self.mRef670 > 0)          & \
                      (self.mRef865 > 0)          & \
                      (self.mRef1240 > 0)         & \
                      (self.mRef1640 > 0)         & \
                      (self.mRef2250 > 0)         & \
                      (self.mSre488 >  0.0)       & \
                      (self.mSre670 >  0.0)       & \
                      (self.mSre412 <  0.0)       

        if algflag is not None:
            fValid = np.zeros(self.iValid.shape).astype(bool)
            for aflag in algflag:
                fValid = fValid | (self.algflag == aflag)
            self.iValid = self.iValid & fValid


        # Filter by additional variables
        # ------------------------------
        self.addFilter(aFilter)
        
        # Reduce the Dataset
        # --------------------
        self.reduce(self.iValid)                    
        self.iValid = np.ones(self.lon.shape).astype(bool)        

        # Outlier removal based on log-transformed AOD
        # --------------------------------------------
        if outliers > 0 :
            self.outlierRemoval(outliers)
            # save the indeces to be used for testing on the outliers later
            self.outValid = np.arange(self.nobs)[self.iValid]

            # Reduce the Dataset
            # --------------------
            self.reduce(self.iValid)
            self.iValid = np.ones(self.lon.shape).astype(bool)
            
        # Angle transforms: for NN work we work with cosine of angles
        # -----------------------------------------------------------
        self.angleTranform()    

#----------------------------------------------------------------------------    
class STATS(object):

    def __init__ (self,K,comblist,nTarget):
        c = max([len(comblist),1])
        if K is None:
            k = 1
        else:
            k = K

        self.slope     = np.ones([k,c,nTarget])*np.nan
        self.intercept = np.ones([k,c,nTarget])*np.nan
        self.R         = np.ones([k,c,nTarget])*np.nan
        self.rmse      = np.ones([k,c,nTarget])*np.nan
        self.mae       = np.ones([k,c,nTarget])*np.nan
        self.me        = np.ones([k,c,nTarget])*np.nan

#---------------------------------------------------------------------
def _train(mxd,expid,c):

    ident  = mxd.ident
    outdir = mxd.outdir

    nHidden  = mxd.nHidden
    topology = mxd.topology[c]

    Input    = mxd.comblist[c]
    Target   = mxd.Target
  
    print("-"*80)
    print("--> nHidden = ", nHidden)
    print("-->  Inputs = ", Input)
  
    n = cpu_count()
    kwargs = {'nproc' : n}
    if mxd.K is None:
        mxd.train(Input=Input,Target=Target,nHidden=nHidden,topology=topology,**kwargs)
        mxd.savenet(outdir+"/"+expid+'_Tau.net')    
    else:
        k = 1
        for iTrain, iTest in mxd.kf.split(np.arange(np.sum(mxd.iValid))):
            I = np.arange(mxd.nobs)
            iValid = I[mxd.iValid]
            mxd.iTrain = iValid[iTrain]
            mxd.iTest  = iValid[iTest]
 
            mxd.train(Input=Input,Target=Target,nHidden=nHidden,topology=topology,**kwargs)
            mxd.savenet(outdir+"/"+expid+'.k={}_Tau.net'.format(str(k)))
            k = k + 1
#--------------------------------------------------------------------------------------

def _test(mxd,expid,c,plotting=True):
    ident  = mxd.ident
    outdir = mxd.outdir    
    if mxd.K is None:
        # figure out the net filename
        if mxd.combinations:
            inputs = expid.split('.')
            found = False
            for invars in itertools.permutations(inputs):
                try: 
                    netFile = outdir+"/"+".".join(invars)+'_Tau.net'
                    mxd.loadnet(netFile)
                    found = True
                    break
                except:
                    pass
            if not found:
                raise('{} not found.  Need to train this combinatin of inputs'.format(netFile))
                
        else:
            invars = mxd.comblist[0]
            netFile = outdir+"/"+".".join(invars)+'_Tau.net'

        # load the net
        mxd.net = mxd.loadnet(netFile)
        mxd.Input = mxd.comblist[c]
        # get statistics and plot
        TestStats(mxd,mxd.K,c)
        if plotting:
            mxd.plotdir = outdir+"/"+".".join(invars)
            mxd.EvaluationPlots(expid,ident,mxd.iTest)
    else:
        # loop through k-folds and test
        k = 1
        for iTrain, iTest in mxd.kf.split(np.arange(np.sum(mxd.iValid))):
            I = np.arange(mxd.nobs)
            iValid = I[mxd.iValid]
            mxd.iTrain = iValid[iTrain]
            mxd.iTest  = iValid[iTest]

            # find the net file
            if mxd.combinations:
                inputs = expid.split('.')
                found = False
                for invars in itertools.permutations(inputs):
                    try: 
                      netFile = outdir+"/"+".".join(invars)+'.k={}_Tau.net'.format(str(k))
                      mxd.loadnet(netFile)
                      found = True
                      print('found file',netFile)
                      break
                    except:
                      pass

                if not found:
                    raise('{} not found.  Need to train this combinatin of inputs'.format(netFile))          
            else:
                invars = mxd.comblist[0]
                netFile = outdir+"/"+".".join(invars)+'.k={}_Tau.net'.format(str(k))

            # load the net
            mxd.net = mxd.loadnet(netFile)
            mxd.Input = mxd.comblist[c]      
            # test and plot
            TestStats(mxd,k-1,c)
            if plotting:
                mxd.plotdir = outdir+"/"+".".join(invars)
                mxd.EvaluationPlots(expid,ident+'.k={}'.format(str(k)),mxd.iTest)
            k = k + 1    

#---------------------------------------------------------------------
def _trainMODIS(mxdx):

    if not mxdx.combinations:
        Input = mxdx.comblist[0]
        _train(mxdx,'.'.join(Input),0)
    else:
        for c,Input in enumerate(mxdx.comblist):
            _train(mxdx,'.'.join(Input),c)

# -------------------------------------------------------------------
def _testMODIS(mxdx):

    if not mxdx.combinations:
        _test(mxdx,mxdx.expid,0,plotting=True)
    else:
        for c,Input in enumerate(mxdx.comblist):
            _test(mxdx,'.'.join(Input),c,plotting=False)

#---------------------------------------------------------------------
def get_combinations(Input_nnr,Input_const):
    comblist   = []
    combgroups = []
    for n in np.arange(len(Input_nnr)):
        for invars in itertools.combinations(Input_nnr,n+1):        
            b = ()
            for c in invars:
                if type(c) is list:
                    b = b + tuple(c)
                else:
                    b = b + (c,)
            #don't do both kinds of abledo together
            if not (('BRF' in b) and ('albedo' in b)):
                if Input_const is not None:
                    comblist.append(tuple(Input_const)+b)
                    combgroups.append((Input_const,)+invars)
                else:
                    comblist.append(b)
                    combgroups.append(invars)

    if Input_const is not None:
        comblist.insert(0,tuple(Input_const))
        combgroups.insert(0,(Input_const,))

    return comblist,combgroups
#---------------------------------------------------------------------
def flatten_list(Input_nnr):
    Input = ()
    for i in Input_nnr:
        if type(i) is list:
            Input = Input + tuple(i)
        else:
            Input = Input + (i,)

    return list(Input)
        
#------------------------------------------------------------------
  
if __name__ == "__main__":

  """
    Example Training/testing
  """
  from   abc_c6_aux           import SummarizeCombinations, SummaryPDFs

  nHidden      = None
  nHLayers     = 1
  combinations = True
  Target       = ['aTau550',]
  Albedo       = ['CoxMunkBRF']
  K            = 2

  filename     = '/nobackup/6/NNR/Training/giant_C6_10km_Terra_20150921.nc'
  retrieval    = 'VSDT_OCEAN'


  doTrain      = True
  doTest       = True
  expid        = 'CoxMunkTest_wSZA'
  Input_const  = ['SolarZenith','ScatteringAngle', 'GlintAngle','mRef470','mRef550','mRef660', 'mRef870','mRef1200','mRef1600','mRef2100']
  Input_nnr    = ['CoxMunkBRF',['fdu','fcc','fsu']]
  aFilter      = ['CoxMunkBRF']
 
  expid        = '{}_{}'.format(retrieval,expid)

  ocean = ABC_Ocean(filename,Albedo=Albedo,verbose=1,aFilter=aFilter)  
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

  if Input_const is not None:
    InputMaster = list((Input_const,) + tuple(Input_nnr))      
  else:
    InputMaster = Input_nnr

  # Do Training and Testing
  # ------------------------
  if doTrain:
    _trainMODIS(ocean)

  if doTest:
    _testMODIS(ocean)

    if combinations:
      SummarizeCombinations(ocean,InputMaster,yrange=None,sortname='slope')
      SummaryPDFs(ocean,varnames=['mRef870','mRef660'])
