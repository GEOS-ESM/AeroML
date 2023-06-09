#!/usr/bin/env python
"""
   Precalculate Cox-Munk albedo from sampled wind parameters according to giant file
   Requires MERRA-2 npz file to be present
   The default is to calculate CX albedo at [470. ,550. ,660. ,870. ,1200.,1600.,2100.]
   This could be changed by supplying calcCoxMunk with the channels option
"""

import os, sys
from pyabc.giant import GIANT
import argparse


if __name__ == '__main__':
    #   Parse command line options
    #   --------------------------
    parser = argparse.ArgumentParser()
    parser.add_argument("giantFile",help="giant spreadhseet file to base sampling on")

    args = parser.parse_args()
    outDir = os.path.dirname(args.giantFile)
    fname = os.path.basename(args.giantFile)
    npzFile = outDir + '/' + fname[:-3] + '_CxAlbedo.npz'
    windFile = outDir + '/' + fname[:-3] + '_MERRA2.npz'

    g = GIANT(args.giantFile)
    g.calcCoxMunk(windFile=windFile,npzFile=npzFile)


