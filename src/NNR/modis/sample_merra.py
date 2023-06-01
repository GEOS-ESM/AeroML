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

    args = parser.parse_args()
    outDir = os.path.dirname(args.giantFile)
    fname = os.path.basename(args.giantFile)
    npzFile = outDir + '/' + fname[:-3] + '_MERRA2.npz'

    g = GIANT(args.giantFile)
    g.sampleMERRA(npzFile=npzFile,Verbose=False)


