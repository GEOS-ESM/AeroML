esma_set_this ()


# these are executable scripts
set (PYSCRIPTS
    create_giant.py
    create_giant_coll.py
    run_create_giant.sh
    run_sampled_cxalbedo.sh
    run_sample_mcd43c1.sh
    run_sample_merra.sh
    sample_cxalbedo.py
    sample_mcd43c1.py
    sample_merra.py
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
    nnr_howto.ipynb
    tavg1_2d_aer_Nx
    tavg1_2d_slv_Nx
    )

install (
    FILES ${train_files} ${OTHERFILES} 
    DESTINATION bin/NNR/${this}
    )
  
