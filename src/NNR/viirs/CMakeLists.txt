esma_set_this ()


# these are executable scripts
set (PYSCRIPTS
    create_giant.py
    download_viirs_laads.sh
    run_create_giant.sh
    run_sample_mcd43c1.sh
    run_sample_merra.sh
    run_sample_geosit.sh
    run_sample_geosit_tqv_to3.sh
    sample_mcd43c1.py
    sample_merra.py
    sample_geosit.py
    sample_geosit_tqv_to3.py
    setup_env.sh
    )

install (
    PROGRAMS  ${PYSCRIPTS}
    DESTINATION bin/NNR/${this}
    )

# Install everything else
# ---------------------
file (GLOB train_files train_*.py)

set (OTHERFILES 
    giantHeader.txt
    tavg1_2d_aer_Nx
    tavg1_2d_slv_Nx
    )

install (
    FILES ${train_files} ${OTHERFILES} 
    DESTINATION bin/NNR/${this}
    )
  
