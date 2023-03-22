esma_set_this ()

# @pcastell TO-DO. Leaving this out from the build for now
# not sure I want hooks into VLIDORT in this repository.
# I think I have a pure python script that can do these calculations somewhere.
#find_package(F2PY3 REQUIRED)
#esma_add_f2py3_module (VLIDORT_BRDF_ABC_
#  SOURCES VLIDORT_BRDF_ABC_py.F90
#  DESTINATION lib/Python/${this}
#  LIBRARIES VLIDORT90
#  INCLUDEDIRS ${CMAKE_CURRENT_BINARY_DIR} ${CMAKE_BINARY_DIR}/lib ${include_${this}} ${esma_include}/VLIDORT90)
#add_dependencies(VLIDORT_BRDF_ABC_ VLIDORT90)

# these are executable scripts
set (PYSCRIPTS
    mcd43c_download.py
    )

install (
    PROGRAMS  ${PYSCRIPTS}
    DESTINATION bin/${this}
    )

# these are non-executaables
set (PYFILES
    abc_avhrr.py
    abc_c6_aux.py
    abc_c6.py
    abc_misr.py
    abc_modis.py
    albedo.py
    anet.py
    aqc_deep.py
    aqc_mapss.py
    brdf.py
    colloc_deep.py
    colloc_misr.py
    evaluate_avhrr.py
    evaluate_cdr.py
    giant.py
    man.py
    mcd43c.py
    nn.py
    reduce_avhrr.py
    synoptic_avhrr.py
    )

file (GLOB CTLFILES ctl/*)

install (
    FILES ${PYFILES} ${CTLFILES} 
    DESTINATION bin/${this}
    )
  
