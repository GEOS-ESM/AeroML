esma_set_this()

set(pythonscripts modis_l2a.py mxd04_l2a.py avhrr_l2a.py patmosx_l2a.py)
install(PROGRAMS ${pythonscripts}  DESTINATION bin)

install(
   FILES mxd04_nnr.py avhrr_nnr.py
   DESTINATION lib/Python
   )


file(GLOB pcf_files *.pcf)

install (
   FILES ${pcf_files}
   DESTINATION etc
   )
