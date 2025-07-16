esma_set_this()

### AVHRR
set(pythonscripts avhrr_l2a.py patmosx_l2a.py)
install(PROGRAMS ${pythonscripts}  DESTINATION bin)

install(
   FILES avhrr_nnr.py
   DESTINATION lib/Python
   )

file(GLOB pcf_files *.pcf)

install (
   FILES ${pcf_files}
   DESTINATION etc
   )

### MODIS 
set(ver v003)
set(pythonscripts modis/${ver}/modis_l2a.py modis/${ver}/mxd04_l2a.py)
install(PROGRAMS ${pythonscripts}  DESTINATION bin)

install(
   FILES modis/${ver}/mxd04_nnr.py
   DESTINATION lib/Python
   )


file(GLOB pcf_files modis/${ver}/*.pcf)

install (
   FILES ${pcf_files}
   DESTINATION etc
   )
