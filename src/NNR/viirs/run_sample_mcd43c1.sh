#!/usr/bin/sh
#=======================================================================
# name - run_sample_mcd43c1.sh
# purpose -
#   This script runs the sample_mcd43c1.py script
#   to interpolate the MCD43C1 dataset to the locations of co-located
#   MODIS and AERONET observations
#   
#   sample_mcd43c1.py is a long running script, it should be run in the background


# SNPP
#---------
terraFile=/nobackup/NNR/Training/002/giant_C002_10km_SNPP_v3.0_20221201.nc
nohup python -u ./sample_mcd43c1.py ${terraFile}  >& nohup.mcd43c1.log &


