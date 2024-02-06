#!/usr/bin/sh
#=======================================================================
# name - run_create_giant.sh
# purpose -
#   This script run the create_giant.py script
#   


# 
#---------
nohup python3 -u ./create_giant.py -I 2012-03-04T00 -E 2012-12-31  >& nohup.giant.2012.log &

list="2013 2014 2015 2016 2017 2018 2019 2020 2021 2022"
for year in $list; do
    nohup python3 -u ./create_giant.py -I ${year}-01-01T00 -E ${year}-12-31  >& nohup.giant.${year}.log &
done


