#!/usr/bin/sh
#=======================================================================
# name - run_sample_cxalbedo.sh
# purpose -
#   This script run the sample_cxalbedo.py script
#   to precalculate the cox munk albedo for the giant spreadsheet
#   
#   This is a long running script, it should be run in the background


# Terra
#---------
terraFile=/nobackup/NNR/Training/061/giant_C061_10km_Terra_v3.0_20211231.nc
nohup python3 -u ./sample_cxalbedo.py ${terraFile}  >& nohup.terra.cxalbedo.log &

# Aqua
#----------
aquaFile=/nobackup/NNR/Training/061/giant_C061_10km_Aqua_v3.0_20211231.nc
nohup python3 -u ./sample_mcd43c1.py ${aquaFile} >& nohup.aqua.mcd43c1.log &

