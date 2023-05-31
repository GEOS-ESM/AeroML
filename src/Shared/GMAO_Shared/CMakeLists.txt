#
# Cmake rules; for now NNR and and eNNR are not installed.
#

# Which sub-directories to descend into
# -------------------------------------
esma_add_subdirectory(GMAO_pyobs)
esma_add_subdirectory(GMAO_mpeu)

# Special case - GMAO_gfio is built twice with two different precisions.
if (EXISTS ${CMAKE_CURRENT_SOURCE_DIR}/GMAO_gfio)
  add_subdirectory (GMAO_gfio GMAO_gfio_r4)
  add_subdirectory (GMAO_gfio GMAO_gfio_r8)
  add_dependencies (GMAO_gfio_r4 GMAO_gfio_r8)
endif ()
