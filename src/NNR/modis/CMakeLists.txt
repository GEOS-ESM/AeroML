esma_set_this ()


# these are executable scripts
set (PYSCRIPTS
    create_giant.py
    create_giant_coll.py
    run_create_giant.sh
    run_sample_cxalbedo.sh
    run_sample_mcd43c1.sh
    run_sample_merra.sh
    run_sample_merra_tqv_to3.sh
    run_sample_geosit.sh
    run_sample_geosit_tqv_to3.sh
    sample_cxalbedo.py
    sample_mcd43c1.py
    sample_merra.py
    sample_merra_tqv_to3.py
    sample_geosit.py
    sample_geosit_tqv_to3.py
    setup_env.sh
    setup_env
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
    nnr_howto.ipynb
    tavg1_2d_aer_Nx
    tavg1_2d_slv_Nx
    slv_tavg_1hr_glo_L576x361_slv
    aer_tavg_3hr_glo_L576x361_slv
    )

install (
    FILES ${train_files} ${OTHERFILES} 
    DESTINATION bin/NNR/${this}
    )
  
