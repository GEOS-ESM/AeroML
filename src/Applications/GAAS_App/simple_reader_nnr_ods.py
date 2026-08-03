import numpy as np
from pyobs import odsreader

class NNRsimplereader:
    def __init__(self, odsfilename, verbose=False):
        self.odsfilename = odsfilename
        self.verbose = verbose

        if self.verbose:
            print(f"Reading ODS file: {self.odsfilename}")

        # Open the ODS file
        ods = odsreader.ODSreader(self.odsfilename, Extra=['omf', 'qchist'])
        
        # Safe exit if no observations
        if ods.nobs < 1:
            raise ValueError(f"No observations found in {self.odsfilename}")

        # Extract levels and dimensions
        self.uniquechannels = np.unique(ods.lev)
        self.nch = len(self.uniquechannels)
        self.nobs = ods.nobs
        self.nlocs = int(self.nobs / self.nch)  # Number of unique lat/lon points

        self.lev = self.uniquechannels
        self.channels = ods.lev
        
        # ---------------------------------------------------------
        # 1D ARRAYS: Metadata mapped to "Location" 
        # Original flat array -> Reshape to (nch, nlocs) -> Take first row
        # ---------------------------------------------------------
        self.lat = ods.lat.reshape(self.nch, self.nlocs)[0, :]
        self.lon = ods.lon.reshape(self.nch, self.nlocs)[0, :]
        self.time = ods.time.reshape(self.nch, self.nlocs)[0, :]
        
        # ---------------------------------------------------------
        # 2D ARRAYS: Data mapped to ("Location", "Channel")
        # Reshape to (nch, nlocs) and transpose so shape is (nlocs, nch)
        # ---------------------------------------------------------
        self.obs = ods.obs.reshape(self.nch, self.nlocs).T
        
        omf_flat = getattr(ods, 'omf', np.zeros(self.nobs))
        self.omf = omf_flat.reshape(self.nch, self.nlocs).T
        
        qch_flat = getattr(ods, 'qchist', np.zeros(self.nobs))
        self.qch = qch_flat.reshape(self.nch, self.nlocs).T
        
        qcx_flat = getattr(ods, 'qcexcl', np.zeros(self.nobs))
        self.qcx = qcx_flat.reshape(self.nch, self.nlocs).T

        if self.verbose:
            print(f"Total obs: {self.nobs} | Unique locations: {self.nlocs} | Channels: {self.nch}")

if __name__ == '__main__':
    odsfile = 'nnr_001.SNPP04_L2a.db_land.20160611_0000z.ods'
    try:
        nnr = NNRsimplereader(odsfilename=odsfile, verbose=True)
    except ValueError as e:
        print(e)
