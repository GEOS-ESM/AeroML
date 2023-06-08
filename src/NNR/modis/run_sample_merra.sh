#!/usr/bin/sh
#=======================================================================
# name - run_sample_merra.sh
# purpose -
#   This script run the sample_merra.py script
#   this reads the giant spreadsheet files of co-located MODIS-AERONET
#   and samples MERRA-2 at these locations
#   


# Terra
#---------
terraFile=/nobackup/NNR/Training/061/giant_C061_10km_Terra_v3.0_20211231.nc
nohup python3 -u ./sample_merra.py ${terraFile}  >& nohup.terra.merra.log &

# Aqua
#----------
aquaFile=/nobackup/NNR/Training/061/giant_C061_10km_Aqua_v3.0_20211231.nc
nohup python3 -u ./sample_merra.py ${aquaFile} >& nohup.aqua.merra.log &

