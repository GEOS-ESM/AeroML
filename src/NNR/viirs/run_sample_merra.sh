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
snppFile=/nobackup/NNR/Training/002/giant_C002_10km_SNPP_v3.0_20221201.nc
nohup python -u ./sample_merra.py ${snppFile}  >& nohup.snpp.merra011.log &


