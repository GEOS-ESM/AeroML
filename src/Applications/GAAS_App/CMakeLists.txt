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
set(pythonscripts modis/modis_l2a.py modis/mxd04_l2a.py)
install(PROGRAMS ${pythonscripts}  DESTINATION bin)

install(
   FILES modis/mxd04_nnr.py
   DESTINATION lib/Python
   )


file(GLOB pcf_files modis/*.pcf)

install (
   FILES ${pcf_files}
   DESTINATION etc
   )

### VIIRS
set(pythonscripts viirs/viirs_l2a.py viirs/vx04_l2a.py)
install(PROGRAMS ${pythonscripts}  DESTINATION bin)

install(
   FILES viirs/vx04_nnr.py
   DESTINATION lib/Python
   )


file(GLOB pcf_files viirs/*.pcf)

install (
   FILES ${pcf_files}
   DESTINATION etc
   )
