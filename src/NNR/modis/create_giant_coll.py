#!/usr/bin/env python3
"""
    Colocate MODIS and AERONET Obs - Create 'Giant Spreadsheet'
    Create seperate giant spreadsheets for each retrieval algorithm
"""

import os,sys
import colocater
from   pyobs.aeronet   import AERONET_L2, granules
from   pyobs.mxd04     import MxD04_L2, MISSING, BEST
from   glob            import glob
from   optparse        import OptionParser   # Command-line args
from   datetime        import datetime, timedelta
from   dateutil.parser import parse as isoparse
from   dateutil.relativedelta import relativedelta
import numpy           as     np
from   netCDF4         import Dataset, stringtoarr, chartostring
from   pyobs.bits      import BITS
from   collections     import OrderedDict
import ast
from   scipy           import stats

CHANNELS  = dict (
                   LAND  = ( 470, 550, 660, 870, 1200, 1600, 2100, 412, 443, 745),
                   OCEAN = ( 470, 550, 660, 870, 1200, 1600, 2100, 412, 443, 745),
                   DEEP  = ( 412, 470, 660 ),
                 )

SCHANNELS = dict (
                   LAND = ( 470, 660, 2100 ),
                   DEEP = ( 412, 470, 660 ),
                )





templateFile = '/nobackup/6/NNR/Training/giant_C6_10km_Aqua_20151005.nc'
STARTDATE    = datetime(2000,0o2,24)

CALCULATOR = {'mode': stats.mode,
              'mean': np.mean,
              'sdev': np.std}

SDS = { 'META': ('Scan_Start_Time',
                'Latitude',
                'Longitude',
                'Solar_Zenith',
                'Solar_Azimuth',
                'Sensor_Zenith',
                'Sensor_Azimuth',
                'Scattering_Angle',
                'Glint_Angle'),
        'DEEP': ('Deep_Blue_Aerosol_Optical_Depth_550_Land',
                'Deep_Blue_Spectral_Aerosol_Optical_Depth_Land',
                'Deep_Blue_Spectral_TOA_Reflectance_Land',
                'Deep_Blue_Spectral_Surface_Reflectance_Land',
                'Deep_Blue_Cloud_Fraction_Land',
                'Deep_Blue_Aerosol_Optical_Depth_550_Land_QA_Flag',
                'Aerosol_Cloud_Fraction_Land',
                'Deep_Blue_Number_Pixels_Used_550_Land'),
        'LAND': ('Corrected_Optical_Depth_Land',
                'Corrected_Optical_Depth_Land_wav2p1',
                'Mean_Reflectance_Land',
                'Surface_Reflectance_Land',
                'Cloud_Fraction_Land',
                'Quality_Assurance_Land',
                'Deep_Blue_Cloud_Fraction_Land',
                'Average_Cloud_Pixel_Distance_Land_Ocean',
                'Number_Pixels_Used_Land'),        
        'OCEAN': ('Effective_Optical_Depth_Best_Ocean',
                'Mean_Reflectance_Ocean',
                'Cloud_Fraction_Ocean',
                'Quality_Assurance_Ocean',
                'Wind_Speed_Ncep_Ocean',
                'Average_Cloud_Pixel_Distance_Land_Ocean',
                'Number_Pixels_Used_Ocean')}

ALIAS = dict( Deep_Blue_Aerosol_Optical_Depth_550_Land = 'aod550',
              Mean_Reflectance_Land = 'reflectance_lnd',
              Surface_Reflectance_Land = 'sfc_reflectance_lnd',
              Aerosol_Cloud_Fraction_Land = 'cloud_lnd',
              Quality_Assurance_Land = 'qa_lnd' )

Inst = dict( Terra = 'MOD04',
             Aqua  = 'MYD04',
           )


ALGO_ALIAS = dict( deep = 'dpbl-l',
                   land = 'corr-l',
                   ocean = 'ea-o',
                   aeronet = 'intrp' )

xMETA = ('nval-o','nval-l','nval-d','nval-a')

xMETA_ANET =  ("Date",
            "Time",
            "Location",
            "Longitude",
            "Latitude",
            "Elevation")

xMETA_MODIS = ( "ISO_DateTime",
            "SolarZenith",
            "SolarAzimuth",
            "SensorZenith",
            "SensorAzimuth",
            "ScatteringAngle",
            "GlintAngle" )

xANET =  OrderedDict([("AOD1640"    , 'AOT_1640'),
                  ("AOD1020"        , 'AOT_1020'), 
                  ("AOD0870"        , 'AOT_870'),
                  ("AOD0670"        , 'AOT_670'),          
                  ("AOD0660intrp"   , 'AOT_660'),
                  ("AOD0550intrp"   , 'AOT_550'),
                  ("AOD0500"        , 'AOT_500'),
                  ("AOD0470intrp"   , 'AOT_470'),
                  ("AOD0440"        , 'AOT_440'),
                  ("AOD0410"        , 'AOT_412'),
                  ("AOD0380"        , 'AOT_380'),
                  ("AOD0340"        , 'AOT_340'),
                  ("WaterVapor", 'Water')])

xLAND = OrderedDict([ ("QA-l",'qa_flag'),
        ("AOD0470corr-l",'aod'),
        ("AOD0550corr-l",'aod'),
        ("AOD0660corr-l",'aod'),
        ("AOD2100corr-l",'Corrected_Optical_Depth_Land_wav2p1'),
        ("mref0412-l",'reflectance'),
        ("mref0443-l",'reflectance'),
        ("mref0470-l",'reflectance'),
        ("mref0550-l",'reflectance'),
        ("mref0660-l",'reflectance'),
        ("mref0745-l",'reflectance'),
        ("mref0870-l",'reflectance'),
        ("mref1200-l",'reflectance'),
        ("mref1600-l",'reflectance'),
        ("mref2100-l",'reflectance'),
        ("surfre0470-l",'sfc_reflectance'),
        ("surfre0660-l",'sfc_reflectance'),
        ("surfre2100-l",'sfc_reflectance'),
        ("acfrac-l",'cloud'),    
        ("cldpixdistavg",'Average_Cloud_Pixel_Distance_Land_Ocean'),
        ("npu0550-l",'Number_Pixels_Used_Land'), 
        ])         

xDEEP = OrderedDict([ ("AOD0412dpbl-l",'aod'),
          ("AOD0470dpbl-l",'aod'),
          ("AOD0550dpbl-l",'aod'),
          ("AOD0660dpbl-l",'aod'),
          ("cfracdpbl-l",'cloud'),
          ("mref0412dpbl-l",'reflectance'),
          ("mref0470dpbl-l",'reflectance'),
          ("mref0660dpbl-l",'reflectance'),
          ("surfre0412dpbl-l",'sfc_reflectance'),
          ("surfre0470dpbl-l",'sfc_reflectance'),
          ("surfre0660dpbl-l",'sfc_reflectance'),
          ("QAdpbl-l",'qa_flag'),
          ("npu0550-d",'Deep_Blue_Number_Pixels_Used_550_Land'),
        ])

xOCEAN = OrderedDict([ ("AOD0470ea-o",'aod'),
          ("AOD0550ea-o",'aod'),
          ("AOD0660ea-o",'aod'),
          ("AOD0870ea-o",'aod'),
          ("AOD1200ea-o",'aod'),
          ("AOD1600ea-o",'aod'),
          ("AOD2100ea-o",'aod'),
          ("mref0470-o",'reflectance'),
          ("mref0550-o",'reflectance'),
          ("mref0660-o",'reflectance'),
          ("mref0870-o",'reflectance'),
          ("mref1200-o",'reflectance'),
          ("mref1600-o",'reflectance'),
          ("mref2100-o",'reflectance'),
          ("wspeed-o",'Wind_Speed_Ncep_Ocean'),
          ("acfrac-o",'cloud'),
          ("QAavg-o",'qa_flag'),
          ("cldpixdistavg",'Average_Cloud_Pixel_Distance_Land_Ocean'),
          ("npu0550-o",'Number_Pixels_Used_Ocean'), 
         ])


# -----------------------------------------------------------------------------

class MODIS(MxD04_L2):
    """ Does QA/QC selections for different MODIS collections """
    def __init__(self,l2_path,prod,algo,year,julday,
                 cloud_thresh=0.70,
                 glint_thresh=40.0,
                 scat_thresh=170.0,
                 only_good=True,
                 coll='061',verbose=0):

        Files = sorted(glob('{}/{}/{}/{}/{}/*hdf'.format(l2_path,coll,prod,year,str(julday).zfill(3))))
        self.rChannels = CHANNELS[algo]
        if algo == 'DEEP': 
            alias = ALIAS
            MxD04_L2.__init__(self,Files,algo,
                              only_good=only_good,
                              SDS=SDS,
                              alias=alias,
                              Verb=verbose)              
        else:
            MxD04_L2.__init__(self,Files,algo,
                              only_good=only_good,
                              SDS=SDS,
                              Verb=verbose)   


        if self.nobs < 1:
            return # no obs, nothing to do

        # Alias time variable
        # --------------------
        self.tyme    = self.Time

        # Q/C
        # ---        
        self.iGood = self.cloud<cloud_thresh 

        for i,c in enumerate(self.rChannels):
            self.iGood = self.iGood & (self.reflectance[:,i]>0)

        if algo in SCHANNELS:
            for i,c in enumerate(self.sChannels):
                self.iGood = self.iGood & (self.sfc_reflectance[:,i]>0)

        if algo == "OCEAN":
            self.iGood = self.iGood & (self.GlintAngle > glint_thresh)

        if algo != "OCEAN":
            self.iGood = self.iGood & (self.ScatteringAngle < scat_thresh)

        # if algo == 'LAND':
        #     self.iGood = self.iGood & (self.Deep_Blue_Cloud_Fraction_Land<cloud_thresh)

        # if algo == 'DEEP':
        #     self.iGood = self.iGood & (self.Aerosol_Cloud_Fraction_Land<cloud_thresh)


        if any(self.iGood) == False:
            print("WARNING: Strange, no good obs left to work with")
            print("Setting nobs to zero")
            self.nobs=0
            return

        # keep only good obs
        self.reduce(self.iGood)

        if algo == 'DEEP':
           self.aod = np.ones((self.nobs,4))
           self.aod[:,0] = self.aod3ch[:,0]
           self.aod[:,1] = self.aod3ch[:,1]
           self.aod[:,2] = self.aod550[:]
           self.aod[:,3] = self.aod3ch[:,2]
# -----------------------------------------------------------------------------

class AERONET(AERONET_L2):
    """ Gets AERONET data """

    def __init__(self,l2_path,date,version,verbose=0):
        
        Files = granules(date,bracket='both',RootDir=l2_path,Version=version.replace('.',''))
        AERONET_L2.__init__(self,Files,Verbose=verbose,version=int(float(version)))
        
        if self.nobs > 0:
            # this fixes the date format for version 3
            self.Date = np.array(['-'.join(d.split(':')[-1::-1]) for d in self.Date])

            iGood = self.AOT_550 >= 0

            self.reduce(iGood)
# -----------------------------------------------------------------------------
class HOLDER(object):
    """empty container for MODIS data"""

    def __init__(self):
        pass
# -----------------------------------------------------------------------------
def createNC(ofile,options):
    # open file for writing
    nc = Dataset(ofile,'w')

    # open template header to get var names and attributes
    s = open('giantHeader.txt', 'r').read()
    header = ast.literal_eval(s)

    # Create global attributes
    nc.date_created = datetime.now().strftime('%Y-%m-%d')
    nc.aeronet_data_type = "Level 2.0"
    nc.satellite_data_type = "MODIS, on {} only".format(options.inst)
    nc.satellite_collection = "Collection {}".format(options.coll)
    nc.aeronet_temporal_averaging = "+/- {} minutes".format(options.Dt)
    nc.satellite_spatial_averaging = "{} km radius around AERONET site".format(options.Dx)
    nc.contact = 'Patricia Castellanos <patricia.castellanos@nasa.gov>'

    # create dimensions
    obs = nc.createDimension('obs',None)
    name_strlen = nc.createDimension('name_strlen',45)

    # create variables
    for algo in ALGO_ALIAS:
        varname = 'nval_AOD0550{}'.format(ALGO_ALIAS[algo])
        varobj = nc.createVariable(varname,header[varname]['datatype'],header[varname]['dimensions'])
        for attr in header[varname]:
            if (attr != 'datatype') & (attr != 'dimensions'):
                varobj.setncattr(attr,header[varname][attr])

    for varname in xMETA_ANET+xMETA_MODIS:
        varobj = nc.createVariable(varname,header[varname]['datatype'],header[varname]['dimensions'])
        for attr in header[varname]:
            if (attr != 'datatype') & (attr != 'dimensions'):
                varobj.setncattr(attr,header[varname][attr])


    for vl in list(xANET.keys())+list(xLAND.keys())+list(xDEEP.keys())+list(xOCEAN.keys()):
        for calc in ['mode','mean','sdev','cval']:
            # don't fuss if it doesn't exist in header
            try:
                varname = calc + '_' + vl

                varobj = nc.createVariable(varname,header[varname]['datatype'],header[varname]['dimensions'],fill_value=-9999.0)
                for attr in header[varname]:
                    if (attr != 'datatype') & (attr != 'dimensions'):
                        varobj.setncattr(attr,header[varname][attr])

            except:
                pass


    return nc
# -----------------------------------------------------------------------------
def writeMETA(iob,nc,algo,anet,mod,anetmatch,modmatch):

    for varname in xMETA_ANET:
        varobj = nc.variables[varname]
        vardata = anet.__dict__[varname]
        if varname in ['Location','Date','Time']:
            varobj[iob] = stringtoarr(vardata[anetmatch[0]],45)
        else:
            varobj[iob] = vardata[anetmatch[0]]

    varobj = nc.variables['nval_AOD0550{}'.format(ALGO_ALIAS['aeronet'])]
    varobj[iob] = len(anetmatch)

    for varname in xMETA_MODIS:
        varobj = nc.variables[varname]
        if varname == 'ISO_DateTime':
            vardata = mod.__dict__[algo].tyme[modmatch]
            dt      = np.array([(t-vardata.min()).total_seconds() for t in vardata])
            isotime = vardata.min() + timedelta(seconds=dt.mean())
            varobj[iob] = stringtoarr(isotime.isoformat(),45)

        else:
            vardata = mod.__dict__[algo].__dict__[varname][modmatch]
            varobj[iob] = vardata.mean()

    varobj = nc.variables['nval_AOD0550{}'.format(ALGO_ALIAS[algo])]
    varobj[iob] = len(modmatch)

# -----------------------------------------------------------------------------
def writeANET(iob,nc,anet,anetmatch):

    # write AERONET variables
    for vl in xANET:
        for calc in ['mode','mean','sdev']:
            # don't fuss if it doesn't exist in header
            found = False
            try:
                varname = calc + '_' + vl   
                varobj = nc.variables[varname]
                found = True
            except:
                pass

            if found:
                vardata = anet.__dict__[xANET[vl]][anetmatch]

                if calc == 'mode':
                    calculator = CALCULATOR[calc]
                    varobj[iob] = calculator(vardata).mode                    
                else:
                    calculator = CALCULATOR[calc]
                    varobj[iob] = calculator(vardata)

# -----------------------------------------------------------------------------

def writeMOD(iob,nc,algo,mod,mmatch,dist):
    if algo == 'land'  : xVARS = xLAND
    if algo == 'deep'  : xVARS = xDEEP
    if algo == 'ocean' : xVARS = xOCEAN
    # Write ocean variables
    for vl in xVARS:
        for calc in ['mode','mean','sdev','cval']:
            # don't fuss if it doesn't exist in header
            found = False
            try:
                varname = calc + '_' + vl  
                varobj = nc.variables[varname] 
                found = True
            except:
                pass

            if found:
                dataname = xVARS[vl]
                if dataname == 'reflectance':
                    #figure out correct index
                    channels = np.array(CHANNELS[algo.upper()])
                    ch = int(vl[4:8])
                    ich = np.argmin(np.abs(channels-ch))
                    vardata = mod.__dict__[algo].__dict__[dataname][:,ich]
                    vardata = vardata[mmatch]
                elif dataname == 'sfc_reflectance':
                    # Figure out correct index
                    channels = np.array(SCHANNELS[algo.upper()])
                    ch = int(vl[6:10])
                    ich = np.argmin(np.abs(channels-ch))
                    vardata = mod.__dict__[algo].__dict__[dataname][:,ich]
                    vardata = vardata[mmatch]
                elif dataname == 'aod':
                    #figure out correct index
                    channels = np.array(mod.__dict__[algo].channels)
                    ch = int(vl[3:7])
                    ich = np.argmin(np.abs(channels-ch))
                    vardata = mod.__dict__[algo].__dict__[dataname][:,ich]
                    vardata = vardata[mmatch]                            
                elif (dataname == 'Number_Pixels_Used_Ocean') or (dataname == 'Number_Pixels_Used_Land'):
                    #figure out correct index
                    channels = np.array(CHANNELS[algo.upper()])
                    ch = int(vl[3:7])
                    ich = np.argmin(np.abs(channels-ch))
                    vardata = mod.__dict__[algo].__dict__[dataname][:,ich]
                    vardata = vardata[mmatch]
                else:
                    vardata = mod.__dict__[algo].__dict__[dataname]
                    vardata = vardata[mmatch]                               

                # calculate value and write to file
                
                if calc == 'cval':
                    imatch = np.argmin(dist)
                    varobj[iob] = vardata[imatch]
                elif calc == 'mode':
                    calculator = CALCULATOR[calc]
                    varobj[iob] = calculator(vardata).mode                    
                else:
                    calculator = CALCULATOR[calc]
                    varobj[iob] = calculator(vardata)



# -----------------------------------------------------------------------------
def writeNC(ofile,algo,mod,anet,match,options):
    """write giant spreadsheet file"""

    # open file to write to
    if options.append:
        nc = Dataset(ofile,'a')
        iob = len(nc.dimensions['obs'])
    else:
        nc = createNC(ofile,options)
        iob = 0
        options.append = True
    

    if match.__dict__[algo].nmatches > 0:
        anetmatch = match.__dict__[algo].stationMatches
        modmatch  = match.__dict__[algo].swathMatches
        distance  = match.__dict__[algo].distance
        for dist,mmatch,amatch in zip(distance,modmatch,anetmatch):
            if (len(amatch) >= 2) & (len(mmatch) >= 5):
                #write META variables
                writeMETA(iob,nc,algo,anet,mod,amatch,mmatch)

                # write AERONET variables
                writeANET(iob,nc,anet,amatch)

                # write LAND, DEEP, or OCEAN variables
                writeMOD(iob,nc,algo,mod,mmatch,dist)



                iob +=1


    nc.close()

if __name__ == '__main__':
    # AERONET temporal averaging interval in minutes (i.e. +/ 30 min)
    Dt = 30
    # MODIS averaging radius around AERONET site in km
    Dx = 27.5

    # Defaults
    outpath  = '/nobackup/NNR/Training/'
    version  = '3.0'

    l2_path  = '/nobackup/MODIS/Level2/'
    inst     = 'Terra'
    coll     = '061'

    anet_path = '/nobackup/AERONET/Level2/ver3'

    isotime = '2000-02-24'
    endisotime = None #'2010-12-31'
    DT      = 2  
    dType   = 'days'
    verbose = False
    overwrite = False
    append_time  = False
    append_var  = False



#   Parse command line options
#   --------------------------
    parser = OptionParser(usage="Usage: %prog algo [options]")

    parser.add_option("-o", "--outpath", dest="outpath", default=outpath,
                      help="Outpath (default=%s)"\
                           %outpath )    

    parser.add_option("-l", "--l2_path", dest="l2_path", default=l2_path,
                      help="MODIS Level2 Path (default=%s)"\
                           %l2_path )

    parser.add_option("-a", "--anet_path", dest="anet_path", default=anet_path,
                      help="AERONET Level2 Path (default=%s)"\
                           %anet_path )    

    parser.add_option("-i", "--inst", dest="inst", default=inst,
                      help="Instrument (default=%s)"\
                           %inst )

    parser.add_option("-I", "--isotime", dest="isotime", default=isotime,
                      help="start isotime (default=%s)"\
                           %isotime )  

    parser.add_option("-E", "--endisotime", dest="endisotime", default=endisotime,
                      help="end isotime (default=%s)"\
                           %endisotime )      

    parser.add_option("-D", "--DT", dest="DT", default=DT,
                      help="delta time for timeseries (default=%s)"\
                           %DT ) 

    parser.add_option("-t", "--dType", dest="dType", default=dType,
                      help="DT type (default=%s)"\
                           %dType )     

    parser.add_option("-V", "--version", dest="version", default=version,
                      help="AERONET version (default=%s)"\
                           %version )     

    parser.add_option("-c", "--coll", dest="coll", default=coll,
                      help="MODIS Collection (default=%s)"\
                           %coll )    

    parser.add_option("-v", "--verbose", dest="verbose", default=verbose,action="store_true",
                      help="verbose (default=%s)"\
                           %verbose )       

    parser.add_option("-O", "--overwrite", dest="overwrite", default=overwrite,action="store_true",
                      help="set this flag to  overwrite existing file (default=%s)"\
                           %overwrite )    

    parser.add_option("--append_time", dest="append_time", default=append_time,action="store_true",
                      help="set this flag to append along time dim for all variable (default=%s)"\
                           %append_time )    

    parser.add_option("--append_var", dest="append_var", default=append_var,action="store_true",
                      help="set this flag to append new variables (default=%s)"\
                           %append_var )    

    parser.add_option("-X", "--Dx", dest="Dx", default=Dx,
                      help="Radius around AERONET site in km (default=%s)"\
                           %Dx ) 

    parser.add_option("-T", "--Dt", dest="Dt", default=Dt,
                      help="time interval for AERONET temporal averaging in minutes (default=%s)"\
                           %Dt )                             

    (options, args) = parser.parse_args()
    
    algo            = args.algo
    prod            = Inst[options.inst]
    nymd            = isoparse(options.isotime)  

    # create outpath if it doesn't exist
    outpath = options.outpath + '/' + options.coll
    if not os.path.exists(outpath):
        os.makedirs(outpath)

    if (options.append_var == False) & (options.append_time == False) & (options.overwrite == False):
        options.newfile = True
    else:
        options.newfile = False

    # figure out if there is an existing file with this version number
    oldfilename = '{}/giant_C{}_10km_{}_{}_v{}_*.nc'.format(outpath,options.coll,algo,options.inst,options.version)
    oldfile = glob(olfilename)

    # if you want to overwrite, remove the existing file
    if options.overwrite & (len(oldfile)>0):
        os.remove(oldfile[0])   
    elif (options.overwrite == False) & (len(oldfile)>0):
        raise Exception("Overwrite is False, but {} exists. Set overwrite to True or change version number".format(oldfilename))

    # if you're creating a new file, or appending to the time dimension, 
    # figure out endtime from passed options
    if options.newfile or options.overwrite or options.append_time:        
        if options.endisotime is None:
            if options.dType == 'days':
                enymd =  nymd + timedelta(days=int(options.DT)) - timedelta(days=1)
            if options.dType == 'months':
                enymd = nymd + relativedelta(months=options.DT)
        else:
            enymd = isoparse(options.endisotime)

    # else if appending a variable, figure out endtime from existing file
    elif options.append_var:
        if len(oldfile) == 0:
            raise Exception('append_var is True, but {}  does not exist'.format(oldfilename))
        else:
            nymd =  oldfile[0][-11:-3]
            enymd = datetime(int(nymd[:4]),int(nymd[4:6]),int(nymd[6:8]))


    # outfile name
    ofile = '{}/giant_C{}_10km_{}_{}_v{}_{}.nc'.format(outpath,options.coll,algo,options.inst,options.version,enymd.strftime('%Y%m%d'))


    # if append_time figure out what dates are in old file
    if options.append_time:
        if len(oldfile) == 0:
            raise Exception('append_time is True, but {} does not exist.'.format(oldfilename))

        # get enddate from file
        nc = Dataset(oldfile[0])
        oldenddate = isoparse(chartostring(nc.variables['ISO_DateTime'][:])[-1]).date()
        oldenddate = datetime(oldenddate.year,oldenddate.month,oldenddate.day)
        nc.close()

        if enymd <= oldenddate:
            raise Exception('append_time is True, but already sampled up to or past this date. Remove {}, or set end date past {}'.format(oldfile[0],enymd.strftime('%Y%m%d')))

        else:
            #figure out starting date
            nymd = oldenddate + timedelta(days=1)
            os.rename(oldfile[0],ofile)

    # loop through days till endtime
    while nymd <= enymd:
        julday   = nymd - datetime(nymd.year,1,1) + timedelta(days=1)
        print('++++Working on ',nymd.strftime('%Y-%m-%d'),' (julday={})'.format(julday.days))

        # get aeronet data
        anet = AERONET(options.anet_path,nymd,options.version,verbose=options.verbose)

        mod  = HOLDER()
        match = HOLDER()
        if anet.nobs > 0:
            # get modis data for each algorithm
            mod  = HOLDER()
            match = HOLDER()
            mod.__dict__[algo] = MODIS(options.l2_path,prod,algo.upper(),nymd.year,julday.days,
                        coll=options.coll,
                        cloud_thresh=0.7,
                        verbose=options.verbose)

            # do colocation
            if mod.__dict__[algo].nobs > 0:
                match.__dict__[algo] = colocater.station_swath(anet,mod.__dict__[algo],Dt=options.Dt,Dx=options.Dx)
            else:
                match.__dict__[algo] = HOLDER()
                match.__dict__[algo].nmatches = 0
                    
        else:
            match.__dict__[algo] = HOLDER()
            match.__dict__[algo].nmatches = 0
            mod.__dict__[algo] = HOLDER()
            mod.__dict__[algo].nobs = 0

        # Write matches to file
        writeNC(ofile,mod,anet,match,options)

        nymd += timedelta(days=1)
