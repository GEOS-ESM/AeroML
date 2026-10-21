esma_set_this()

### IODA
set(pythonscripts script_offline_ods.py)
install(PROGRAMS ${pythonscripts}  DESTINATION bin)

install(
   FILES simple_reader_nnr_ods.py writeIODA.py
   DESTINATION lib/Python
   )

### AVHRR
set(pythonscripts avhrr_l2a.py patmosx_l2a.py)
install(PROGRAMS ${pythonscripts}  DESTINATION bin)

install(
   FILES avhrr_nnr.py
   DESTINATION lib/Python
   )

file(GLOB perl_files CONFIGURE_DEPENDS *.pl)
file(GLOB pcf_files CONFIGURE_DEPENDS *.pcf)

install (
   FILES ${pcf_files}
   DESTINATION etc
   )

install (
   PROGRAMS ${perl_files}
   DESTINATION bin
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
