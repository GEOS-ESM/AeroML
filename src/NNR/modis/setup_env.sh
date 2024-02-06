#!/usr/bin/sh
#=======================================================================
# name - setup_env.bash
# purpose -
#   This script can be "sourced" from the bash shell to set environment
#   variables and modules needed for building and running the GEOS system.
#

# Add AeroApps to the path
#----------------
export AERODIR=$HOME/workspace/AeroML_update_viirs_nnr/AeroML
PATH=${AERODIR}/install/bin/NNR/:${PATH}
PATH=${AERODIR}/install/bin/NNR/modis/:$PATH

# Set Python PATH
#-----------------
export PYTHONPATH=${AERODIR}/install/lib
export PYTHONPATH=${AERODIR}/install/lib/Python:$PYTHONPATH
export PYTHONPATH=${AERODIR}/install/lib/Python/pyabc:$PYTHONPATH
export PYTHONPATH=${AERODIR}/install/lib/Python/pyobs:$PYTHONPATH

# source AeroApps modules
source ${AERODIR}/env@/g5_modules.sh

# Path for shared object libraries
#------------------
export LD_LIBRARY_PATH=${AERODIR}/install/lib:$LD_LIBRARY_PATH
export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:${BASEDIR}/`uname -s`/lib

# Link what we need for this project
#------------------------------------
export BIN=${AERODIR}/install/bin/NNR/modis
files=(create_giant_coll.py create_giant.py giantHeader.txt sample_cxalbedo.py sample_mcd43c1.py sample_merra.py sample_merra_tqv_to3.py)
for fname in "${files[@]}"
do
  if [ ! -h $fname ]
  then
    ln -s ${BIN}/$fname .
  fi
done

files=(giantHeader.txt tavg1_2d_aer_Nx tavg1_2d_slv_Nx)
for fname in "${files[@]}"
do
  if [ ! -h $fname ] 
  then
    ln -s ${BIN}/${fname} .
  fi
done

# Copy what we need for this project
# but don't overwrite if already setup
# -------------------------------------
files=(run_create_giant.sh run_sample_cxalbedo.sh run_sample_mcd43c1.sh run_sample_merra.sh run_sample_merra_tqv_to3.sh )
for fname in "${files[@]}"
do
  if [ ! -f $fname ]
  then
    cp ${BIN}/$fname .
  fi
done

files=(train_deep.py train_land.py train_ocean.py)
for fname in "${files[@]}"
do
  if [ ! -f $fname ]
  then
    cp ${BIN}/$fname .
  fi
done

