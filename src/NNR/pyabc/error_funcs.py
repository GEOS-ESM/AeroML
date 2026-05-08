"""
   This module contains error functions

   P. Castellanos, 2016.

"""

import numpy                as      np

# ---
def rmse(predictions, targets):
    return np.sqrt((np.square(predictions - targets)).mean(axis=0))
# ---
def mae(predictions, targets):
    return np.abs(predictions-targets).mean(axis=0)
# ---
def me(predictions, targets):
    return (predictions-targets).mean(axis=0)    

