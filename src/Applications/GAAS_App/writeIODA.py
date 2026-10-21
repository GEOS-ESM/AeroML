#!/usr/bin/env python3

import numpy as np
from datetime import datetime
from netCDF4 import Dataset

class WriteIODA:
    def __init__(self, nnr=None, filename="ioda_output_file.nc4", convert_log_to_linear=False, verbose=True):
        self.filename = filename
        self.verbose = verbose
        self.convert_log_to_linear = convert_log_to_linear
        
        if nnr is None:
            raise ValueError("Must provide an NNRsimplereader object (nnr)")
        
        self.nnr = nnr

    def write_ioda(self):
        if self.verbose:
            print(f'[x] Working on file: {self.filename}')

        nloc = self.nnr.nlocs
        nch = self.nnr.nch

        # Standard JEDI / NetCDF Fill Values
        JEDI_FILL_FLOAT = 9.969209968386869e+36
        JEDI_FILL_INT32 = -2147483647
        JEDI_FILL_INT64 = -9223372036854775806

        # --- LOG CONVERSION LOGIC ---
        if self.convert_log_to_linear:
            if self.verbose: print("[x] Converting Obs and HofX from log space (exp(x)-0.01) back to AOD space...")
            obs_data = np.exp(self.nnr.obs) - 0.01
            
            # Since HofX = Obs - OMF (in whichever space they currently exist),
            # we calculate HofX in log space first, then convert the result to AOD space.
            hofx_log = self.nnr.obs - self.nnr.omf
            hofx_data = np.exp(hofx_log) - 0.01
        else:
            obs_data = self.nnr.obs
            hofx_data = self.nnr.obs - self.nnr.omf

        # Using 'with' ensures the file safely closes even if a crash occurs
        with Dataset(self.filename, "w", format="NETCDF4") as ioda:
            
            # 1. Global Attributes
            ioda.description = "Multi-wavelength NNR AOD data written in JEDI/IODA file format"
            ioda.source = "NASA/GMAO"

            # 2. Global Dimensions
            ioda.createDimension("Channel", nch)
            ioda.createDimension("Location", nloc)

            # 3. Global Variables
            channel = ioda.createVariable("Channel", "i4", ("Channel",), fill_value=JEDI_FILL_INT32)
            location = ioda.createVariable("Location", "i4", ("Location",), fill_value=JEDI_FILL_INT32)
            channel[:] = np.arange(1, nch + 1)
            location[:] = np.arange(1, nloc + 1)

            # 4. MetaData Group
            metadata = ioda.createGroup("MetaData")
            
            time_var = metadata.createVariable("dateTime", "i8", ("Location",), fill_value=JEDI_FILL_INT64)
            time_var.units = "seconds since 1970-01-01T00:00:00Z"
            
            lat_var = metadata.createVariable("latitude", "f4", ("Location",), fill_value=JEDI_FILL_FLOAT)
            lat_var.units = "degrees_north"
            
            lon_var = metadata.createVariable("longitude", "f4", ("Location",), fill_value=JEDI_FILL_FLOAT)
            lon_var.units = "degrees_east"
            
            wav_var = metadata.createVariable("obs_wavelength", "f4", ("Channel",), fill_value=JEDI_FILL_FLOAT)
            wav_var.units = "nm"

            # Fast, vectorized time conversion
            epoch = datetime(1970, 1, 1)
            time_var[:] = np.array([(t - epoch).total_seconds() for t in self.nnr.time])
            lat_var[:] = self.nnr.lat
            lon_var[:] = self.nnr.lon
            wav_var[:] = np.unique(self.nnr.lev)

            # 5. Data Groups
            groups_data = {
                "ObsValue": obs_data,
                "ObsError": np.ones((nloc, nch)) * 0.18,
                "PreQc": self.nnr.qcx,
                "HistQc": self.nnr.qch,
                "EffectiveQc": np.zeros((nloc, nch)),
                "HofX": hofx_data
            }

            # Loop to cleanly build all identical 2D variables
            for grp_name, data in groups_data.items():
                grp = ioda.createGroup(grp_name)
                
                # Assign float32 for most, but keep QC variables as integers if desired
                if "Qc" in grp_name:
                    var = grp.createVariable("aerosolOpticalDepth", "i4", ("Location", "Channel"), fill_value=JEDI_FILL_INT32)
                else:
                    var = grp.createVariable("aerosolOpticalDepth", "f4", ("Location", "Channel"), fill_value=JEDI_FILL_FLOAT)
                
                if grp_name == "ObsValue":
                    var.units = "1"
                    
                var[:] = data

        if self.verbose:
            print(f"[✓] IODA file successfully written with JEDI fill values to {self.filename}.")
