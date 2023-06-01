#!/usr/bin/sh
#=======================================================================
# name - setup_env.sh
# purpose -
#   This script can be "sourced" from the bash shell to set environment
#   variables and modules needed for building and running in the
#   AeroApps environment
#

# Add AeroApps to the path
#----------------
export AERODIR=${HOME}/workspace/AeroApps_nnr-updates/AeroApps
PATH=${AERODIR}/install/bin/NNR/:$PATH
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
export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:${BASEDIR}/${ARCH}/lib:${GEOSDIR}/lib

