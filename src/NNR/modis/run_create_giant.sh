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
nohup python3 -u ./create_giant.py -N -E 2021-12-31 >& nohup.terra.log &

# Aqua
#----------
#nohup python3 -u ./create_giant.py -N --inst Aqua -I 2002-07-04 -E 2021-12-31 >& nohup.aqua.log &


