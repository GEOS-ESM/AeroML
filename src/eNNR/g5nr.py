#!/bin/env python

import os
import sys

from types     import *
from datetime  import date, datetime, timedelta
import numpy   as np
from dateutil.parser import parse as isoparse

from npz       import NPZ

Wavelengths = ( '360', '380', '410', '550', '670', '870', '1550', '1650' )
    
Meta =  ( # "Latitude",
          # "Longitude",
          "SolarZenith",
          "SolarAzimuth",
          "SensorZenith",
          "SensorAzimuth",
          # "ScatteringAngle"
          # "GlintAngle",
         )

# Basic: without polarization
# ---------------------------
Target = ( 'Tau355', 'Tau440', 'Tau550', 'Tau870' ) 
Features = (  'Ref360',   # TOA Reflectances
              'Ref380',
              'Ref410',
              'Ref550',
              'Ref670',
              'Ref870',
              # 'Ref940',
              # 'Ref1230', 
              # 'Ref1380',
              'Ref1550',
              'Ref1650',
              'Sre360',  # Surface Reflectanes
              'Sre380',
              'Sre410',
              'Sre550',
              'Sre670',
              'Sre870',
              # 'Sre940',
              # 'Sre1230', 
              # 'Sre1380',
              'Sre1550',
              'Sre1650',
              )

# Advanced: use polarization information
# --------------------------------------
pTarget = Target + ('Tau_a355', 'Tau_a440', 'Tau_a550', 'Tau_a870' ) 

pFeatures = Features + \
            ( 'I360', # I
              'I380',
              'I410',
              'I550',
              'I670',
              'I870',
              'I940',

              'I1230',
              'I1380',
              'I1550',
              'I1650',
              'U360',   # U
              'U380',
              'U410',
              'U550',
              'U670',
              'U870',
#              'U940'
#              'U1230', 
#              'U1380',
              'U1550',
              'U1650',
              'Q360',   # Q
              'Q380',
              'Q410',
              'Q550',
              'Q670',
              'Q870',
#              'Q940',
#              'Q1230', 
#              'Q1380',
              'Q1550',
              'Q1650',    # Polarized Surface Reflectance: Q
              'SreQ360',
              'SreQ380',
              'SreQ410',
              'SreQ550',
              'SreQ670',
              'SreQ870',
#              'SreQ940',
#              'SreQ1230', 
#              'SreQ1380',
              'SreQ1550',
              'SreQ1650',
              'SreU360',     # Polarized Surface Reflectance: U
              'SreU380',
              'SreU410',
              'SreU550',
              'SreU670',
              'SreU870',
#              'SreU940',
#              'SreU1230',
#              'SreU1380',
              'SreU1550',
              'SreU1650',
              )


Alias = dict(
           Latitude  = 'lat',
           Longitude = 'lon',
        )

MISSING = 1E15

class G5NR(object):

  """
      Read Level-2 GIANT Co-located AERONET/MODIS/VIIRS aerosol files from
      GSFC MODIS group.
  """


  def __init__ (self,Files,Names):
    """
     Creates an GIANT object defining the attributes corresponding
     to the SDS of interest.
    """

    self.variables = []

    # Ingest select data
    # ------------------
    for filename in Files:
      
      f = np.load(filename)

      for v in f:
        print(v)
      
      for name in Names:
        
        v = f[name]
        rank = len(v.shape)
        if rank == 1:
          data = v[:]
        elif rank==2:
          data = v[:,:]
        elif rank==3:
          data = v[:,:,:]
        else:
          raise ValueError('variable %s has invalid rank %d'%(name,rank))
        if name in Alias:
          name = self.ALias[name]

        self.__dict__[name] = data
        self.variables.append(name)

      f.close()

    # Compute key angles
    # ------------------
    d2r = np.pi / 180.
    r2d = 180. / np.pi
    if 'SensorZenith' in self.variables:

      # Glint angle
      # -----------
      RelativeAzimuth = np.abs(self.SolarAzimuth - self.SensorAzimuth - 180.)
      cosGlintAngle   = np.cos(self.SolarZenith*d2r) * np.cos(self.SensorZenith*d2r) + \
                        np.sin(self.SolarZenith*d2r) * np.sin(self.SensorZenith*d2r) * \
                        np.cos(RelativeAzimuth*d2r)        
      J = (np.abs(cosGlintAngle)<=1.0)
      self.GlintAngle = MISSING * np.ones(cosGlintAngle.shape)
      self.GlintAngle[J] = np.arccos(cosGlintAngle[J])*r2d
       
      # Scattering angle
      # ----------------
      cosScatAngle  = -np.cos(self.SolarZenith*d2r) * np.cos(self.SensorZenith*d2r) + \
                       np.sin(self.SolarZenith*d2r) * np.sin(self.SensorZenith*d2r) * \
                       np.cos(RelativeAzimuth*d2r)
      J = (abs(cosScatAngle)<=1.0)
      self.ScatteringAngle = MISSING * np.ones(cosScatAngle.shape)
      self.ScatteringAngle[J] = np.arccos(cosScatAngle[J])*r2d

      self.variables += [ 'GintAngle', 'ScatteringAngle' ]
      
    # Record number of observations
    # -----------------------------
    self.nobs = 

#---
  def reduce(self,I):
    """
    Reduce observations according to index I. 
    """
    for name in self.variables:
      q = self.__dict__[name]
      #print "{} Reducing "+name,q.shape
      self.__dict__[name] = q[I]

    self.nobs = self.variables.shape[0]


#---
  def toDataFrame(self,Vars=None,index='tyme'):
        """
        Return variables as a DataFrame.
        """
        import pandas as pd
        VARS = dict()
        if Vars is None:
            for name in self.variables:
                VARS[name] = self.__dict__[name]
        else:
            for name in Vars:
                VARS[name] = self.__dict__[name]
                    
        df = pd.DataFrame(VARS,index=self.__dict__[index])
        df[df==MISSING] = np.nan
        return df
           
#---

class TARGET(G5NR):
    """
    Handle targets, typically AOD and absorption AOD (AAOD).
    """
    def __init__(self,Files=None,GlintTresh=40.):
        """
        Read files and optionally provide Q/C.
        """
        if Files is None:
            Files = ['data/inclined.target.npz','data/polar.target.npz'],
        G5NR.__init__(self,Files=Files, Names=Meta+Target)
        self.reduce(self.filter(GlintTresh=GlintTresh))

    def filter(self,GlintTresh=40.):

        iValid = ones(self.nobs,dtype=bool)

        # Check Tau
        # ---------

        # If any of the angles are bad, toss out the other angles
        # -------------------------------------------------------
        iValid = iValid.prod(axis=1).astype(bool)

        return iValid
        
class FEATURES(G5NR):
    """
    Handle features, reflectances and angles.
    """
    def __init__(self,Files=None,GlintTresh=40.):
        """
        Read files and optionally provide Q/C.
        """
        if Files is None:
            Files = ['data/inclined.features.npz','data/polar.features.npz']
        G5NR.__init__(self,Files=Files,Names=Meta+Features)

        self.reduce(self.filter(GlintTresh=GlintTresh))

    def filter(self,GlintTresh=40.):
        """
        Return indices of good observations.
        """
        
        iValid = ones(self.GlintAngle.shape,dtype=bool)

        # Angles
        # ------
        iValid = iValid \
               & ( np.abs(self.GlintAngle)      != MISSING ) \
               & ( np.abs(self.ScatteringAngle) != MISSING ) \
               & ( self.GlintAngle > GlintThresh)

        # For each wavelength
        # -------------------
        for wave in Wavelengths:

            # TOA
            # ---
            R = self.__dict__('Ref'+wave)
            I = self.__dict__('I'+wave)
            U = self.__dict__('U'+wave)
            Q = self.__dict__('Q'+wave)

            iValid = iValid \
                   & (R>=0) & (I>=0) & (U>=0) & (Q>=10) \
                   & (R<10) & (I<10) & (U<10) & (Q<10)

            # Surface
            # -------
            R = self.__dict__('Sre'+wave)
            U = self.__dict__('SreU'+wave)
            Q = self.__dict__('SreQ'+wave)

            iValid = iValid \
                   & (R>=0) & (U>=0) & (Q>=10) \
                   & (R<10) & (U<10) & (Q<10)


        # If any of the angles are bad, toss out the other angles
        # -------------------------------------------------------
        iValid = iValid.prod(axis=1).astype(bool)

        # All done, return indices of good observatins
        # --------------------------------------------
        return iValid
        
# .....................................................................

if __name__ == "__main__":

    aqua = 'data/giant_C6_10km_Aqua_20151005.nc'
    terra = 'data/giant_C6_10km_Terra_20150921.nc'

    filename = terra
    
#    lnd = LAND(filename)
    ocn = OCEAN(filename)
#    dpb = DEEP(filename)


