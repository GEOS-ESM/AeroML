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
nohup python3 -u ./create_giant.py -I 2000-02-24 -E 2000-12-31 >& nohup.terra.2000.log &

list="2001 2002 2003 2004 2005 2006 2007 2008 2009 2010"
#list="2011 2012 2013 2014 2015 2016 2017 2018 2019 2020"
#list="2021 2022 2023"
for year in $list; do
    nohup python3 -u ./create_giant.py -I ${year}-01-01 -E ${year}-12-31 >& nohup.terra.${year}.log &
done 

# Aqua
#----------
nohup python3 -u ./create_giant.py --inst Aqua -I 2002-07-04 -E 2002-12-31 >& nohup.aqua.2002.log &

list="2003 2004 2005 2006 2007 2008 2009 2010"
#list="2011 2012 2013 2014 2015 2016 2017 2018 2019 2020"
#list="2021 2022 2023"
for year in $list; do
    nohup python3 -u ./create_giant.py --inst Aqua -I ${year}-01-01 -E ${year}-12-31 >& nohup.aqua.${year}.log &
done


