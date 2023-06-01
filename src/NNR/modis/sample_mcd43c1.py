#!/usr/bin/env python
"""
   Sample MCD43C1 BRDF parameters  according to giant file
"""

import os, sys
from giant import GIANT
import argparse


if __name__ == '__main__':
    #   Parse command line options
    #   --------------------------
    parser = argparse.ArgumentParser()
    parser.add_argument("giantFile",help="giant spreadhseet file to base sampling on")

    args = parser.parse_args()
    outDir = os.path.dirname(args.giantFile)
    fname = os.path.basename(args.giantFile)
    npzFile = outDir + '/' + fname[:-3] + '_MCD43C1.npz'

    g = GIANT(args.giantFile)
    g.sampleMCD43C(npzFile=npzFile,Verbose=True)


