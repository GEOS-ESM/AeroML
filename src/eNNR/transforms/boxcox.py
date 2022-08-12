"""
   Implements normalized Box-Cox transport and its inverse.
"""


import pandas as pd
from scipy import stats
import scipy.special as special

EPSILON = 1e-2  # tolerances


def nBoxCox(x):
    """
    Returns normalized (z-scores) BoxCox transform.
    """
    (x_,p_)=stats.boxcox(x)
    p = (p_, x_.mean(), x_.std() )
    x_ = (x_-p[1]) / p[2]
    return (x_,p)
    
def inv_nBoxCox(x,p):
    """
    Inverse normalized (z-scores) BoxCox transform.
    """
    x_ = p[1] + p[2] * x 
    x_ = special.inv_boxcox(x_,p[0])
    return x_

class Transform(object):
    """
    Implemented Box-Cox transform on features and targets.
    """
    def __init__(self,features,target,eps=EPSILON):
        """
           Apply Box-Cox transform on simulations of reflectances and AOD.

        On input, Panda data frames with features and targets.
        On output, attributes holding transformed data and corresponding 
        metadata needed for the inverse.

        """

        # Transform features
        # ------------------
        self.features = features.copy()
        self.mFeatures =  pd.DataFrame(columns=features.columns)
        for a in features.columns:
            if a[:3]=="Ref" or a[:4]=="mRef": # only transform reflectance
                self.features[a], self.mFeatures[a] = nBoxCox(features[a])
            else:
                self.features[a], self.mFeatures[a] = features[a], None

        # Transform target (handle zero or negative targets)
        # --------------------------------------------------
        self.target = target.copy()
        self.mTarget =  pd.DataFrame(columns=target.columns)
        for a in self.target.columns:
            if self.target[a].min() <= 0:
                self.target[a] += self.eps
                shift = eps # shift AOD to avoid division by zero
            else:
                shift = 0.0 # no shift
            self.target[a], p = nBoxCox(target[a])
            self.mTarget[a] = p + (shift,)  # record shift for inverse

    def copy(self,target=None):
        """
        Copy the transformed data and metadata, possibily overwriting target
        (say, with results of an estimation.)
        """
        B = BoxCox(eps=self.eps)
        B.features = self.features.copy()
        if target is None:
            B.target = self.target.copy()
        else:
            B.target = target.copy()
               
    def inverse(self):
        """
        Return inverse transform. On output, data frames with features and target.
        """
        features = self.features.copy()
        target = self.copy.copy()

        # Features
        # --------
        for a in self.features:
            if mFeatures[a] is not None:
                features[a] = inv_nBoxCox(self.features[a],self.mFeatures[a])

        # Target
        # ------
        for a in self.target:
            shift = self.mTarget[a][3]
            target[a] = inv_nBoxCox(self.target[a],self.mTarget[a])
            target[a] += shift
            
                                             
        return(features,target)
        
#-----------------------------------------------------------------------------

if __name__ == "__main__":

    import sys
    sys.path.append('..')
    import matplotlib.pyplot as plt

   
    
