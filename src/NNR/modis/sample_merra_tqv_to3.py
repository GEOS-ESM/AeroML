#!/usr/bin/env python3
"""
   Sample MERRA-2 according to giant file
"""

import os, sys
from pyabc.giant import GIANT
import argparse


if __name__ == '__main__':
    #   Parse command line options
    #   --------------------------
    parser = argparse.ArgumentParser()
    parser.add_argument("giantFile",help="giant spreadhseet file to base sampling on")
    parser.add_argument("syear",help="start year")
    parser.add_argument("eyear",help="end year")

    args = parser.parse_args()
    outDir = os.path.dirname(args.giantFile)
    fname = os.path.basename(args.giantFile)
#    npzFile = outDir + '/' + fname[:-3] + '_MERRA2_TQV_TO3.npz'
    npzFile = outDir + '/' + fname[:-3] + '_MERRA2_TQV_TO3_{}_{}.npz'.format(args.syear,args.eyear)

    g = GIANT(args.giantFile)
    g.sampleMERRA(npzFile=npzFile,Verbose=False,aer_x=None,onlyVars=('TQV','TO3'))


