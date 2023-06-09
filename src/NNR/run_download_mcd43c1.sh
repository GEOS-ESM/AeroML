#!/usr/bin/sh
#=======================================================================
# name - run_downlaod_mcd43c1.sh
# purpose -
#   This script runs the mcd43c_download.py script
#   


nohup python3 -u .//mcd43c_download.py 2022-01-01T00 2022-05-31  >& nohup.download.mcd43c1.log &


