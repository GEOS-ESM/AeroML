#
# Cmake rules; for now NNR and and eNNR are not installed.
#

# Which sub-directories to descend into
# -------------------------------------
  esma_add_subdirectory(Shared)
  esma_add_subdirectory(NNR)
  esma_add_subdirectory(Applications)

# Install 'abc' package
# ---------------------
file (GLOB abc_files pyabc/*.py)
install (
    FILES ${abc_files}
    DESTINATION lib/Python/pyobs
    )
