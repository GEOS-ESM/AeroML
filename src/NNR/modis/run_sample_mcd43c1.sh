#!/usr/bin/sh
#=======================================================================
# name - run_create_giant.sh
# purpose -
#   This script run the create_giant.py script
#   to make the giant spreadsheet files of co-located
#   MODIS and AERONET observations
#   
#   This is a long running script, it should be run in the background


# Terra
#---------
terraFile=/nobackup/NNR/Training/061/giant_C061_10km_Terra_v3.0_20211231.nc
nohup python3 -u ./sample_mcd43c1.py ${terraFile}  >& nohup.terra.mcd43c1.log &

# Aqua
#----------
aquaFile=/nobackup/NNR/Training/061/giant_C061_10km_Aqua_v3.0_20211231.nc
nohup python3 -u ./sample_mcd43c1.py ${aquaFile} >& nohup.aqua.mcd43c1.log &

