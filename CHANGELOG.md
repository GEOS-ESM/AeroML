# ChangeLog

## [Unreleased]
### Added

### Fixed

### Changed

 
## [v1.5.0] 2026-01-22
### Changed

- Minor changes to get VIIRS to work in ADAS v5.43x
- Move setup_gaas_obs.pl from GMAO_Etc here for consistency
- chmod +x pl script

## [v1.4.0] 2025-12-03

### Added
- added option to specify which VIIRS collection is used
- added option to use DT cloud fraction to filter DB
- added option to filter out DB obs in a DT ob is available
- added NOAA20 to kx list
- update training to include VIIRS DT and NOAA-20
- add balancing of inputs and outputs based on quartiles for training
- added configuration files for the NOAA-20 v001 NNR model
- added a "standard" pcf file for MODIS and NOAA-20 that contains the standard data stream paths
 
### Changed
- Updated GMAOpyobs to v1.5.0
- Updated the NOAA20 pcf files to GEOS-FP paths

## [v1.3.0] 2025-07-25
### Added
- add MAPL needed by nnr scripts

### Fixed

### Changed
- remove duplicate GMAO_Shared scripts.  Now use GMAO_Shared repo imported through components
- Updates to some NNR scripts that came from last merge commits in AeroApps


## [v1.2.0] 2025-07-16
### Added

- abiltity to use GEOS-IT for training
- split up giant files into multiple files
- update GMAOpyobs to v1.0.8
- fix some issues in testing plots from using AE fits for training
- 2 pathways for for VIIRS land pixels training
- add 412 and 440 ch to modis ocean NNR
- ability to train on the AE linear fit to spectral AOD on MODIS 
- AE linear fit training also extended to VIIRS
- GAAS_App now contains the updated v004 modis GAAS_App scripts and the v001 viirs scripts. these were brought over from AeroApps
- modis and viirs GAAS_App scripts are now organized by version numbers to allow for legacy back compatibility/reproducibiity

### Fixed

### Changed

- update all components to SLES15 versions

## [v1.1.0] 2025-07-02

### Added

- create an Applications folder for GAAS_App scripts that do the NNR pre-processing for the DAS
- ability to train on the AE linear fit to spectral AOD
- use TQV and TO3 as inputs

### Fixed

- Minor fix associated with installation location of software.

### Changed

- updated GMAOpyobs to latest v1.0.5
- Update to ESMA_env v4.8.2 (Fixes for RHEL8 GMAO Machines)

## [v1.0.0] 2023-06-07

### Added

- Constructing AeroML from bits and pieces of AeroApps
- Added changelog enforcer and YAML validator

### Fixed

### Changed

- import GMAOpyobs through components.yaml

### Added
   
### Changed 
   
