#!/usr/bin/sh
#=======================================================================
# name - run_sample_geosit.sh
# purpose -
#   This script run the sample_geosit.py script
#   this reads the giant spreadsheet files of co-located MODIS-AERONET
#   and samples GEOS-IT at these locations
#   


# Terra
#---------
giantFile=./002/giant_C002_10km_SNPP_v3.0_20120304_20121231.nc
nohup python3 -u ./sample_geosit.py ${giantFile}  2012-03-04 2012-12-31 >& nohup.geosit.2012.log &


list="2013 2014 2015 2016 2017 2018 2019 2020 2021 2022"
for year in $list; do
    giantFile=./002/giant_C002_10km_SNPP_v3.0_${year}0101_${year}1231.nc
    nohup python3 -u ./sample_geosit.py ${giantFile}  ${year}-01-01 ${year}-12-31 >& nohup.geosit.${year}.log &
done
