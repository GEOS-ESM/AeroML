#!/usr/bin/sh
#=======================================================================
# name - run_sample_geosit_tqv_to3.sh
# purpose -
#   This script run the sample_geosit_tqv_to3.py script
#   this reads the giant spreadsheet files of co-located MODIS-AERONET
#   and samples GEOS-IT at these locations
#   


# Terra
#---------
terraFile=./giant_C061_10km_Terra_v3.0_20221231.nc
#nohup python3 -u ./sample_geosit_tqv_to3.py ${terraFile}  >& nohup.terra.tqv_to3.log &

#nohup python3 -u ./sample_geosit_tqv_to3.py ${terraFile} 2000 2001 >& nohup.terra.merra.2000.log &
#nohup python3 -u ./sample_geosit_tqv_to3.py ${terraFile} 2001 2002 >& nohup.terra.merra.2001.log &
#nohup python3 -u ./sample_geosit_tqv_to3.py ${terraFile} 2002 2003 >& nohup.terra.merra.2002.log &
#nohup python3 -u ./sample_geosit_tqv_to3.py ${terraFile} 2003 2004 >& nohup.terra.merra.2003.log &
#nohup python3 -u ./sample_geosit_tqv_to3.py ${terraFile} 2004 2005 >& nohup.terra.merra.2004.log &
#nohup python3 -u ./sample_geosit_tqv_to3.py ${terraFile} 2005 2006 >& nohup.terra.merra.2005.log &
#nohup python3 -u ./sample_geosit_tqv_to3.py ${terraFile} 2006 2007 >& nohup.terra.merra.2006.log &
#nohup python3 -u ./sample_geosit_tqv_to3.py ${terraFile} 2007 2008 >& nohup.terra.merra.2007.log &
#nohup python3 -u ./sample_geosit_tqv_to3.py ${terraFile} 2008 2009 >& nohup.terra.merra.2008.log &
#nohup python3 -u ./sample_geosit_tqv_to3.py ${terraFile} 2009 2010 >& nohup.terra.merra.2009.log &
#nohup python3 -u ./sample_geosit_tqv_to3.py ${terraFile} 2010 2011 >& nohup.terra.merra.2010.log &

#nohup python3 -u ./sample_geosit_tqv_to3.py ${terraFile} 2011 2012 >& nohup.terra.merra.2011.log &
#nohup python3 -u ./sample_geosit_tqv_to3.py ${terraFile} 2012 2013 >& nohup.terra.merra.2012.log &
#nohup python3 -u ./sample_geosit_tqv_to3.py ${terraFile} 2013 2014 >& nohup.terra.merra.2013.log &
#nohup python3 -u ./sample_geosit_tqv_to3.py ${terraFile} 2014 2015 >& nohup.terra.merra.2014.log &
#nohup python3 -u ./sample_geosit_tqv_to3.py ${terraFile} 2015 2016 >& nohup.terra.merra.2015.log &
#nohup python3 -u ./sample_geosit_tqv_to3.py ${terraFile} 2016 2017 >& nohup.terra.merra.2016.log &
#nohup python3 -u ./sample_geosit_tqv_to3.py ${terraFile} 2017 2018 >& nohup.terra.merra.2017.log &
#nohup python3 -u ./sample_geosit_tqv_to3.py ${terraFile} 2018 2019 >& nohup.terra.merra.2018.log &
#nohup python3 -u ./sample_geosit_tqv_to3.py ${terraFile} 2019 2020 >& nohup.terra.merra.2019.log &

#nohup python3 -u ./sample_geosit_tqv_to3.py ${terraFile} 2020 2021 >& nohup.terra.merra.2020.log &
#nohup python3 -u ./sample_geosit_tqv_to3.py ${terraFile} 2021 2022 >& nohup.terra.merra.2021.log &
#nohup python3 -u ./sample_geosit_tqv_to3.py ${terraFile} 2022 2023 >& nohup.terra.merra.2022.log &


# Aqua
#----------
aquaFile=./giant_C061_10km_Aqua_v3.0_20221231.nc
#nohup python3 -u ./sample_geosit_tqv_to3.py ${aquaFile} >& nohup.aqua.tqv_to3.log &

#nohup python3 -u ./sample_geosit_tqv_to3.py ${aquaFile} 2002 2003 >& nohup.aqua.merra.2002.log &
#nohup python3 -u ./sample_geosit_tqv_to3.py ${aquaFile} 2003 2004 >& nohup.aqua.merra.2003.log &
#nohup python3 -u ./sample_geosit_tqv_to3.py ${aquaFile} 2004 2005 >& nohup.aqua.merra.2004.log &
#nohup python3 -u ./sample_geosit_tqv_to3.py ${aquaFile} 2005 2006 >& nohup.aqua.merra.2005.log &
#nohup python3 -u ./sample_geosit_tqv_to3.py ${aquaFile} 2006 2007 >& nohup.aqua.merra.2006.log &
#nohup python3 -u ./sample_geosit_tqv_to3.py ${aquaFile} 2007 2008 >& nohup.aqua.merra.2007.log &
#nohup python3 -u ./sample_geosit_tqv_to3.py ${aquaFile} 2008 2009 >& nohup.aqua.merra.2008.log &
#nohup python3 -u ./sample_geosit_tqv_to3.py ${aquaFile} 2009 2010 >& nohup.aqua.merra.2009.log &
#nohup python3 -u ./sample_geosit_tqv_to3.py ${aquaFile} 2010 2011 >& nohup.aqua.merra.2010.log &

nohup python3 -u ./sample_geosit_tqv_to3.py ${aquaFile} 2011 2012 >& nohup.aqua.merra.2011.log &
nohup python3 -u ./sample_geosit_tqv_to3.py ${aquaFile} 2012 2013 >& nohup.aqua.merra.2012.log &
nohup python3 -u ./sample_geosit_tqv_to3.py ${aquaFile} 2013 2014 >& nohup.aqua.merra.2013.log &
nohup python3 -u ./sample_geosit_tqv_to3.py ${aquaFile} 2014 2015 >& nohup.aqua.merra.2014.log &
nohup python3 -u ./sample_geosit_tqv_to3.py ${aquaFile} 2015 2016 >& nohup.aqua.merra.2015.log &
nohup python3 -u ./sample_geosit_tqv_to3.py ${aquaFile} 2016 2017 >& nohup.aqua.merra.2016.log &
nohup python3 -u ./sample_geosit_tqv_to3.py ${aquaFile} 2017 2018 >& nohup.aqua.merra.2017.log &
nohup python3 -u ./sample_geosit_tqv_to3.py ${aquaFile} 2018 2019 >& nohup.aqua.merra.2018.log &
nohup python3 -u ./sample_geosit_tqv_to3.py ${aquaFile} 2019 2020 >& nohup.aqua.merra.2019.log &

nohup python3 -u ./sample_geosit_tqv_to3.py ${aquaFile} 2020 2021 >& nohup.aqua.merra.2020.log &
nohup python3 -u ./sample_geosit_tqv_to3.py ${aquaFile} 2021 2022 >& nohup.aqua.merra.2021.log &
nohup python3 -u ./sample_geosit_tqv_to3.py ${aquaFile} 2022 2023 >& nohup.aqua.merra.2022.log &

