#!/usr/bin/sh
#=======================================================================
# name - download_viir_laads.sh 
# purpose -
#   This script uses wget to download VIIRS data from LAADS
#   


# SNPP or NOAA20
#-----------------
SAT=SNPP
sat=snpp

rootDir=/nobackup/VIIRS/AERDB/${SAT}/002/Level2
url=https://ladsweb.modaps.eosdis.nasa.gov/archive/allData/5200/AERDB_L2_VIIRS_${SAT}

mkdir -p ${rootDir}/

# leap years
# 2016 2020
for year in 2012 
do
    for day in {66..366}
    do
        if (( $day < 10 )); then
            julday=00${day}
        fi
        if (($day >= 10 && $day <= 99)); then
            julday=0${day}
        fi
        if (( $day >= 100 )); then
            julday=${day}
        fi  

        echo "wget -e robots=off -m -np -R .html,.tmp -nH --cut-dirs=4 "${url}/${year}/${julday}/" --header "Authorization: Bearer ${laads_token}" -P ${rootDir}/"

        wget -e robots=off -m -np -R .html,.tmp -nH --cut-dirs=4 "${url}/${year}/${julday}/" --header "Authorization: Bearer ${laads_token}" -P ${rootDir}/

    done
done

# non-leap years
for year in 2013 2014 2015 2017 2018 2019 2021 2022
do
    for day in {1..365}
    do
        if (( $day < 10 )); then
            julday=00${day}
        fi
        if (($day >= 10 && $day <= 99)); then
            julday=0${day}
        fi
        if (( $day >= 100 )); then
            julday=${day}
        fi

        echo "wget -e robots=off -m -np -R .html,.tmp -nH --cut-dirs=4 "${url}/${year}/${julday}/" --header "Authorization: Bearer ${laads_token}" -P ${rootDir}/"

        wget -e robots=off -m -np -R .html,.tmp -nH --cut-dirs=4 "${url}/${year}/${julday}/" --header "Authorization: Bearer ${laads_token}" -P ${rootDir}/


    done
done
