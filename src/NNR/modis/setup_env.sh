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
export AERODIR=/home/pcastell/workspace/AeroApps_nnr-updates/AeroApps
PATH=${AERODIR}/install/bin/:$PATH
PATH=${AERODIR}/install/bin/ABC/:$PATH
PATH=${AERODIR}/install/bin/GAAS_App/:$PATH

# Set Python PATH
#-----------------
export PYTHONPATH=${AERODIR}/install/lib
export PYTHONPATH=${AERODIR}/install/lib/Python:$PYTHONPATH
export PYTHONPATH=${AERODIR}/install/lib/Python/ABC:$PYTHONPATH
export PYTHONPATH=${AERODIR}/install/lib/Python/pyods:$PYTHONPATH
export PYTHONPATH=/home/pcastell/workspace/ABC:$PYTHONPATH
export PYTHONPATH=${AERODIR}/install/bin/ABC:$PYTHONPATH
export PYTHONPATH=${AERODIR}/install/bin/GAAS_App:$PYTHONPATH
export PYTHONPATH=${AERODIR}/install/bin/:$PYTHONPATH

# source AeroApps modules
source ${AERODIR}/env@/g5_modules.sh

# Path for shared object libraries
#------------------
export LD_LIBRARY_PATH=${AERODIR}/install/lib:$LD_LIBRARY_PATH
export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:${BASEDIR}/${ARCH}/lib:${GEOSDIR}/lib

