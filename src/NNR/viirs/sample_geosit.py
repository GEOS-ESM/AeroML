#!/usr/bin/env python3
"""
   Sample GEOS-IT according to giant file
"""

import os, sys
from pyabc.giant_viirs import GIANT
import argparse


if __name__ == '__main__':
    #   Parse command line options
    #   --------------------------
    parser = argparse.ArgumentParser()
    parser.add_argument("giantFile",help="giant spreadhseet file to base sampling on")
    parser.add_argument("sdate",help="start date")
    parser.add_argument("edate",help="end date")

    args = parser.parse_args()
    outDir = os.path.dirname(args.giantFile)
    fname = os.path.basename(args.giantFile)
    npzFile = outDir + '/' + fname[:-3] + '_GEOSIT_{}_{}.npz'.format(args.sdate.replace('-',''),args.edate.replace('-',''))

    g = GIANT(args.giantFile)
    g.sampleMERRA(slv_x='slv_tavg_1hr_glo_L576x361_slv',aer_x='aer_tavg_3hr_glo_L576x361_slv',npzFile=npzFile,Verbose=True)


