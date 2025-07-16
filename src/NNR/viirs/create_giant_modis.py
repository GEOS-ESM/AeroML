#!/usr/bin/env python3
"""
    Colocate MODIS and VIIRS Obs - Create 'Giant Spreadsheet'
"""

import os,sys
from   pyabc import colocater
from   pyobs.vx04      import Vx04_L2, MISSING, BEST, CHANNELS, SDS
from   glob            import glob
from   optparse        import OptionParser   # Command-line args
from   datetime        import datetime, timedelta
from   dateutil.parser import parse as isoparse
from   dateutil.relativedelta import relativedelta
import numpy           as     np
from   netCDF4         import Dataset, stringtoarr, chartostring
from   collections     import OrderedDict
import ast
from   scipy           import stats
from   binObs_   import binobs2d, binobs3d, binobscnt3d

CALCULATOR = {'mode': stats.mode,
              'mean': np.mean,
              'sdev': np.std}


SCHANNELS = {'DT_LAND': ( 480., 670., 2250. ),
             'DB_LAND': ( 412., 488., 670. ),
             'DB_DEEP': ( 412., 488., 670. ),
            }

ALGO_ALIAS = dict( db_land = 'dpbl-l',
                   db_deep = 'dpbl-l',
                   db_ocean = 'dpbl-o',
                   dt_land = 'corr-l',
                   dt_ocean = 'ea-o',
                   aeronet = 'intrp' )

#ALGOS = ['dt_land',
#         'dt_ocean',
#         'db_land',
#         'db_ocean',
#         ]

ALGOS = ['db_land',
         'db_deep',
         'db_ocean',
         ]

xMETA = ('nval-o','nval-l','nval-d','nval-a')

xMETA_MOD = ("Longitude","Latitude","Date","Time")

xMOD =  OrderedDict([("AOD0870"        , 'AOT_870'),
                  ("AOD0660intrp"   , 'AOT_660'),
                  ("AOD0550intrp"   , 'AOT_550'),
                  ("AOD0470intrp"   , 'AOT_470'),
                  ("AOD0440"        , 'AOT_440')])

xMETA_VIIRS = ( "ISO_DateTime",
            "SolarZenith",
            "SensorZenith",
            "ScatteringAngle",
            "GlintAngle",
            "RelativeAzimuth")

mchannels = [440,470,550,660,870]

xDT_LAND = OrderedDict([ ("QA-l",'qa_flag'),
        ("AOD0480corr-l",'aod'),
        ("AOD0550corr-l",'aod'),
        ("AOD0670corr-l",'aod'),
        ("AOD2250corr-l",'aod'),
#        ("mref0412-l",'reflectance'),
#        ("mref0443-l",'reflectance'),
        ("mref0480-l",'reflectance'),
#        ("mref0550-l",'reflectance'),
        ("mref0670-l",'reflectance'),
#        ("mref0745-l",'reflectance'),
#        ("mref0870-l",'reflectance'),
#        ("mref1200-l",'reflectance'),
#        ("mref1600-l",'reflectance'),
        ("mref2250-l",'reflectance'),
        ("surfre0480-l",'sfc_reflectance'),
        ("surfre0670-l",'sfc_reflectance'),
        ("surfre2250-l",'sfc_reflectance'),
        ("acfrac-l",'cloud'),    
#        ("cldpixdistavg",'Average_Cloud_Pixel_Distance_Land_Ocean'),
        ])         

xDT_OCEAN = OrderedDict([ ("AOD0480ea-o",'aod'),
          ("AOD0550ea-o",'aod'),
          ("AOD0670ea-o",'aod'),
          ("AOD0860ea-o",'aod'),
          ("AOD1240ea-o",'aod'),
          ("AOD1600ea-o",'aod'),
          ("AOD2250ea-o",'aod'),
          ("mref0480-o",'reflectance'),
          ("mref0550-o",'reflectance'),
          ("mref0670-o",'reflectance'),
          ("mref0860-o",'reflectance'),
          ("mref1240-o",'reflectance'),
          ("mref1600-o",'reflectance'),
          ("mref2250-o",'reflectance'),
          ("acfrac-o",'cloud'),
          ("QAavg-o",'qa_flag'),
         ])

xDB_LAND = OrderedDict([ ("AOD0412dpbl-l",'aod'),
          ("AOD0488dpbl-l",'aod'),
          ("AOD0550dpbl-l",'aod'),
          ("AOD0670dpbl-l",'aod'),
          ("AOD2250dpbl-l",'aod'),
          ("cfracdpbl-l",'cloud'),
          ("mref0412dpbl-l",'reflectance'),
          ("mref0488dpbl-l",'reflectance'),
          ("mref0550dpbl-l",'reflectance'),
          ("mref0670dpbl-l",'reflectance'),
          ("mref0865dpbl-l",'reflectance'),
          ("mref1240dpbl-l",'reflectance'),
          ("mref1640dpbl-l",'reflectance'),
          ("mref2250dpbl-l",'reflectance'),
          ("surfre0412dpbl-l",'sfc_reflectance'),
          ("surfre0488dpbl-l",'sfc_reflectance'),
          ("surfre0670dpbl-l",'sfc_reflectance'),
          ("QAdpbl-l",'qa_flag'),
          ("algflgdpbl-l",'Algorithm_Flag_Land'),
          ("atypedpbl-l","Aerosol_Type_Land"),
          ("NDVIdpbl-l","NDVI"),
          ("Total_Column_Ozonedpbl-l","Total_Column_Ozone"),
          ("PrecipitableWaterdpbl-l","Precipitable_Water"),
          ("Elevationdpbl-l","pixel_elevation"),
        ])

xDB_OCEAN = OrderedDict([ ("AOD0488dpbl-o",'aod'),
          ("AOD0550dpbl-o",'aod'),
          ("AOD0670dpbl-o",'aod'),
          ("AOD0865dpbl-o",'aod'),
          ("AOD1240dpbl-o",'aod'),
          ("AOD1640dpbl-o",'aod'),
          ("AOD2250dpbl-o",'aod'),
          ("cfracdpbl-o",'cloud'),
          ("mref0412dpbl-o",'reflectance'),
          ("mref0488dpbl-o",'reflectance'),
          ("mref0550dpbl-o",'reflectance'),
          ("mref0670dpbl-o",'reflectance'),
          ("mref0865dpbl-o",'reflectance'),
          ("mref1240dpbl-o",'reflectance'),
          ("mref1640dpbl-o",'reflectance'),
          ("mref2250dpbl-o",'reflectance'),
          ("wspeed-o",'Wind_Speed'),
          ("QAdpbl-o",'qa_flag'),
          ("algflgdpbl-o",'Algorithm_Flag_Ocean'),
          ("atypedpbl-o","Aerosol_Type_Ocean"),
          ("Total_Column_Ozonedpbl-o","Total_Column_Ozone"),
          ("PrecipitableWaterdpbl-o","Precipitable_Water"),
        ])

# -----------------------------------------------------------------------------

class VIIRS(Vx04_L2):
    """ Does QA/QC selections for different VIIRS collections """
    def __init__(self,l2_path,inst,algo,date,
                 cloud_thresh=0.10,
                 glint_thresh=40.0,
                 scat_thresh=170.0,
                 only_good=True,
                 coll='002',verbose=0):

        Algo, surface = algo.split('_')
        if inst == 'SNPP':
            prod = 'VNPAER{}'.format(Algo)
        elif 'NOAA' in inst:
            prod = 'VN{}AER{}'.format(inst[-2:],Algo)

        ds = date - timedelta(hours=2)
        de = date + timedelta(hours=2)

        Files = []
        while ds <= de:
            jday = ds.strftime('%j')
            hh   = ds.strftime('%H')
            year = ds.strftime('%Y')
            Files += sorted(glob('{}/Level2/{}/{}/{}/{}/*A{}{}.{}*nc'.format(l2_path,prod,coll,year,jday,year,jday,hh)))
            

            ds += timedelta(hours=1)

        if algo == 'DB_DEEP':
            algo_ = 'DB_LAND'
        else:
            algo_ = algo
        Vx04_L2.__init__(self,Files,algo_,
                              only_good=only_good,
                              SDS=SDS,
                              Verb=verbose)

        if self.nobs < 1:
            return # no obs, nothing to do

        # Q/C
        # ---        
        self.iGood = self.cloud<cloud_thresh 

        for i,c in enumerate(self.rChannels):
            self.iGood = self.iGood & (self.reflectance[:,i]>0)

        if surface == "DEEP":
            for i,c in enumerate(self.sChannels):
                self.iGood = self.iGood & ~self.sfc_reflectance[:,i].mask
        elif surface == "LAND":
            # 412 surface reflectance not used for vegetated surfaces
            self.iGood = self.iGood & self.sfc_reflectance[:,0].mask & ~self.sfc_reflectance[:,1].mask & ~self.sfc_reflectance[:,2].mask


        if surface == "OCEAN":
            self.iGood = self.iGood & (self.GlintAngle > glint_thresh)
        else:
            self.iGood = self.iGood & (self.ScatteringAngle < scat_thresh)

        if any(self.iGood) == False:
            print("WARNING: Strange, no good obs left to work with")
            print("Setting nobs to zero")
            self.nobs=0
            return

        # keep only good obs
        self.reduce(self.iGood)

        if (algo == 'DB_LAND') or (algo == 'DB_DEEP'):
           self.aod = np.ones((self.nobs,4))
           self.aod[:,0] = self.aod3ch[:,0]
           self.aod[:,1] = self.aod3ch[:,1]
           self.aod[:,2] = self.aod550[:]
           self.aod[:,3] = self.aod3ch[:,2]

        # Create a pseudo cloud fraction for Deep Blue
        if Algo == 'DB':
            self.cloud = 1. - self.npixels_used.astype(float)/self.npixels_valid.astype(float) 

        # Alias time variable
        # --------------------
        self.tyme    = self.Time
        dt = self.tyme - date
        DT = np.array([tt.total_seconds()/60 for tt in dt])
        self.DT = DT
# -----------------------------------------------------------------------------

class MODIS(object):
    """ Gets MODIS data from ODS files"""

    def __init__(self,ods_path,date,prod,inst,vnnr,im,jm,verbose=0):
        self.im = im
        self.jm = jm
        self.mchannels = mchannels
        #initialize varaibles to be read in
        for ch in self.mchannels:
            self.__dict__['odsAOT_'+str(ch)] = []

        SDS = ['lon','lat','tyme','DT']
        for sds in SDS:
            self.__dict__[sds] = []

        yyyymm = '{}'.format(date.strftime('Y%Y/M%m'))
        yyyymm_hh = '{}'.format(date.strftime('%Y%m%d_%H00'))
        Files = sorted(glob(ods_path+'/{}/nnr_{}.{}04_L2a.{}.{}z.ods'.format(yyyymm,vnnr,inst,prod,yyyymm_hh)))
        
        for fname in Files:
            nc = Dataset(fname)
            print(fname)
            if nc.dimensions['nbatches'].size > 0:
                lev = nc.variables['lev'][:].ravel()
                tau = nc.variables['obs'][:].ravel()
                lon = np.array(nc.variables['lon'][:]).ravel()*0.01
                lat = np.array(nc.variables['lat'][:]).ravel()*0.01
                # get time
                time = nc.variables['time'][:].ravel() 
                tunits = nc.variables['time'].units.split()[2:]
                t0 = isoparse(tunits[0]+'T'+tunits[1])
                tyme= np.array([t0 + timedelta(minutes=int(tt)) for tt in time[~time.mask]])
                dt = tyme - date
                DT = np.array([tt.total_seconds()/60 for tt in dt])

                # get rid of masked values
                lev = lev[~time.mask]
                tau = tau[~time.mask]
                lon = lon[~time.mask]
                lat = lat[~time.mask]

                for ch in self.mchannels:
                    i = lev == ch
                    self.__dict__['odsAOT_'+str(ch)].append(tau[i])

                # limit the lon and lat arrays
                self.lon.append(lon[i])
                self.lat.append(lat[i])
                self.tyme.append(tyme[i])
                self.DT.append(DT[i])

                #alias
                self.Longitude = self.lon
                self.Latitude = self.lat

        if len(self.tyme) > 0:
            # concatenate
            for sds in SDS:
                self.__dict__[sds] = np.concatenate(self.__dict__[sds])
           
            for ch in self.mchannels:
                self.__dict__['odsAOT_'+str(ch)] = np.concatenate(self.__dict__['odsAOT_'+str(ch)])

            self.nobs = len(self.tyme)
        else:
            self.nobs = 0


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
    nc.satellite_data_type = "VIIRS, on {} only".format(options.inst)
    nc.satellite_collection = "Collection {}".format(options.coll)
    nc.temporal_window = "+/- {} minutes".format(options.Dt)
    nc.ods_gridding = "nlon = {}, nlat = {} ".format(options.im,options.jm)
    nc.contact = 'Patricia Castellanos <patricia.castellanos@nasa.gov>'

    # create dimensions
    obs = nc.createDimension('obs',None)
    name_strlen = nc.createDimension('name_strlen',45)

    # create variables
    for algo in ALGO_ALIAS:
        if algo == 'db_deep':
            pass
        else:
            varname = 'nval_AOD0550{}'.format(ALGO_ALIAS[algo])
            varobj = nc.createVariable(varname,header[varname]['datatype'],header[varname]['dimensions'])
            for attr in header[varname]:
                if (attr != 'datatype') & (attr != 'dimensions'):
                    varobj.setncattr(attr,header[varname][attr])

    for varname in xMETA_MOD + xMETA_VIIRS:
        varobj = nc.createVariable(varname,header[varname]['datatype'],header[varname]['dimensions'])
        for attr in header[varname]:
            if (attr != 'datatype') & (attr != 'dimensions'):
                varobj.setncattr(attr,header[varname][attr])


    for vl in list(xMOD.keys())+list(xDT_LAND.keys())+list(xDB_LAND.keys())+list(xDT_OCEAN.keys())+list(xDB_OCEAN.keys()):
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
def writeMETA(iob,nc,algo,mod,viir,modmatch,viirmatch):

    for varname in xMETA_VIIRS:
        varobj = nc.variables[varname]
        if varname == 'ISO_DateTime':
            vardata = viir.__dict__[algo].tyme[viirmatch]
            dt      = np.array([(t-vardata.min()).total_seconds() for t in vardata])
            isotime = vardata.min() + timedelta(seconds=dt.mean())
            varobj[iob] = stringtoarr(isotime.isoformat(),45)

        else:
            vardata = viir.__dict__[algo].__dict__[varname][viirmatch]
            varobj[iob] = vardata.mean()


# -----------------------------------------------------------------------------
def writeMOD(iob,nc,mod,modmatch):

    # write MODIS variables
    # grid first

    for varname in xMETA_MOD:
        varobj = nc.variables[varname]
        if varname in ['Date','Time']:
            odsdata = mod.DT
            vardata = binobs2d(mod.lon,mod.lat,odsdata,mod.im,mod.jm,MISSING)
            vardata = vardata.ravel()[np.concatenate(modmatch)]
            nobs = len(vardata)

            tyme = np.array([mod.nymd + timedelta(minutes=int(dt)) for dt in vardata])
            if varname == 'Date':
                wdata = np.array([tt.strftime('%Y-%m-%d') for tt in tyme])
            else:
                wdata = np.array([tt.strftime('%H:%M') for tt in tyme])

            varobj[iob:iob+nobs] = np.array([stringtoarr(w,45) for w in wdata])
        else:
            odsdata = mod.__dict__[varname]
            vardata = binobs2d(mod.lon,mod.lat,odsdata,mod.im,mod.jm,MISSING)
            vardata = vardata.ravel()[np.concatenate(modmatch)]
            nobs = len(vardata)            
            varobj[iob:iob+nobs] = vardata

    for vl in xMOD:
        for calc in ['mean']:
            # don't fuss if it doesn't exist in header
            found = False
            try:
                varname = calc + '_' + vl   
                varobj = nc.variables[varname]
                found = True
            except:
                pass

            if found:
                odsdata = mod.__dict__['ods'+xMOD[vl]]
                vardata = binobs2d(mod.lon,mod.lat,odsdata,mod.im,mod.jm,MISSING)
                vardata = vardata.ravel()[np.concatenate(modmatch)]

                nobs = len(vardata)
                varobj[iob:iob+nobs] = vardata

# -----------------------------------------------------------------------------

def writeVIIRS(iob,nc,algo,viir,vmatch):
    if algo == 'dt_land'  : xVARS = xDT_LAND
    if algo == 'db_land'  : xVARS = xDB_LAND
    if algo == 'db_deep'  : xVARS = xDB_LAND
    if algo == 'dt_ocean' : xVARS = xDT_OCEAN
    if algo == 'db_ocean' : xVARS = xDB_OCEAN
    # Write ocean variables
    for vl in xVARS:
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
                dataname = xVARS[vl]
                if dataname == 'reflectance':
                    #figure out correct index
                    channels = viir.__dict__[algo].rChannels
                    ch = int(vl[4:8])
                    ich = np.argmin(np.abs(channels-ch))
                    vardata = viir.__dict__[algo].__dict__[dataname][:,ich]
                    vardata = vardata[vmatch]
                elif dataname == 'sfc_reflectance':
                    # Figure out correct index
                    channels = np.array(SCHANNELS[algo.upper()])
                    ch = int(vl[6:10])
                    ich = np.argmin(np.abs(channels-ch))
                    vardata = viir.__dict__[algo].__dict__[dataname][:,ich]
                    vardata = vardata[vmatch]
                elif dataname == 'aod':
                    #figure out correct index
                    channels = np.array(viir.__dict__[algo].channels)
                    ch = int(vl[3:7])
                    ich = np.argmin(np.abs(channels-ch))
                    vardata = viir.__dict__[algo].__dict__[dataname][:,ich]
                    vardata = vardata[vmatch]                            
                else:
                    vardata = viir.__dict__[algo].__dict__[dataname]
                    vardata = vardata[vmatch]                               

                # calculate value and write to file
                
                if calc == 'mode':
                    calculator = CALCULATOR[calc]
                    varobj[iob] = calculator(vardata).mode                    
                else:
                    calculator = CALCULATOR[calc]
                    varobj[iob] = calculator(vardata)



# -----------------------------------------------------------------------------
def writeNC(ofile,algo,viir,mod,match,options):
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
        modmatch = match.__dict__[algo].odsMatches
        viirmatch  = match.__dict__[algo].swathMatches

        # write AERONET variables
        writeMOD(iob,nc,mod.__dict__[algo],modmatch)
        for mmatch,vmatch in zip(modmatch,viirmatch):
            #write META variables
            writeMETA(iob,nc,algo,mod,viir,mmatch,vmatch)


            # write LAND, DEEP, or OCEAN variables
            writeVIIRS(iob,nc,algo,viir,vmatch)

            iob +=1



    nc.close()

if __name__ == '__main__':
    # Temporal colocation (i.e. +/ 30 min)
    Dt = 30
    # spatial resolution of gridding for overlaps
    Dx = 0.1  

    # Defaults
    outpath  = '/nobackup/NNR/Training/'
    version  = '1.0'

    l2_path  = '/nobackup/VIIRS/'
    inst     = 'SNPP'
    coll     = '002'

    mod_path = '/nobackup/NNR/netfiles_py3/nnr_043_MYD04_061_1hr/Level2/'
    vnnr     = '043'

    isotime = '2019-08-01'
    endisotime = None #'2010-12-31'
    DT      = 1
    dType   = 'days'
    verbose = False
    overwrite  = False


#   Parse command line options
#   --------------------------
    parser = OptionParser(usage="Usage: %prog [options]")

    parser.add_option("-o", "--outpath", dest="outpath", default=outpath,
                      help="Outpath (default=%s)"\
                           %outpath )    

    parser.add_option("-l", "--l2_path", dest="l2_path", default=l2_path,
                      help="VIIRS Level2 Path (default=%s)"\
                           %l2_path )

    parser.add_option("-a", "--mod_path", dest="mod_path", default=mod_path,
                      help="MODIS Level2 (ods) Path (default=%s)"\
                           %mod_path )    

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
                      help="VIIRS Collection (default=%s)"\
                           %coll )    

    parser.add_option("-v", "--verbose", dest="verbose", default=verbose,action="store_true",
                      help="verbose (default=%s)"\
                           %verbose )       

    parser.add_option("--overwrite", dest="overwrite", default=overwrite,action="store_true",
                      help="overwrite existing file (default=%s)"\
                           %overwrite ) 

    parser.add_option("-X", "--Dx", dest="Dx", default=Dx,
                      help="Resolution for gridding overlaps (default=%s)"\
                           %Dx ) 

    parser.add_option("-T", "--Dt", dest="Dt", default=Dt,
                      help="time interval for colocation in minutes (default=%s)"\
                           %Dt )                             

    (options, args) = parser.parse_args()
    
    nymd            = isoparse(options.isotime)  

    if options.endisotime is None:
        if options.dType == 'days':
            enymd =  nymd + timedelta(days=int(options.DT)) - timedelta(hours=1)
        if options.dType == 'months':
            enymd = nymd + relativedelta(months=options.DT)
    else:
        enymd = isoparse(options.endisotime)


    # create outpath if it doesn't exist
    outpath = options.outpath + '/' + options.coll
    if not os.path.exists(outpath):
        os.makedirs(outpath)

    options.append = False       

    # grid resolution
    im = int(360. / options.Dx)
    jm = int(180. / options.Dx + 1)   
    options.im = im
    options.jm = jm

    while nymd <= enymd:
        julday   = nymd - datetime(nymd.year,1,1) + timedelta(days=1)
        print('++++Working on ',nymd.strftime('%Y-%m-%d'),' (julday={})'.format(julday.days))


        # outfile name
        ofile = '{}/giant_myd_C{}_{}_v{}_{}.nc'.format(outpath,options.coll,options.inst,options.version,
                                                       nymd.strftime('%Y%m%d%H'))
        if os.path.exists(ofile) and (options.overwrite is False):
            raise Exception('Outfile {} exists. Set --overwrite flag to clobber file'.format(ofile))        

        # get MODIS data
        mod = HOLDER()
        for algo in ALGOS:
            mod.__dict__[algo] = MODIS(options.mod_path,nymd,algo[3:],'MYD',vnnr,im,jm,verbose=options.verbose)
        
        viir  = HOLDER()
        match = HOLDER()
        for algo in ALGOS: 
            if mod.__dict__[algo].nobs > 0:
                # get viirs data 
                viir.__dict__[algo] = VIIRS(options.l2_path,options.inst,algo.upper(),nymd,
                        coll=options.coll,
                        cloud_thresh=0.7,
                        verbose=options.verbose)                

                # do colocation
                if viir.__dict__[algo].nobs > 0:
                    match.__dict__[algo] = colocater.ods_swath(mod.__dict__[algo],viir.__dict__[algo],Dt=options.Dt)
                else:
                    match.__dict__[algo] = HOLDER()
                    match.__dict__[algo].nmatches = 0
                    
            else:
                match.__dict__[algo] = HOLDER()
                match.__dict__[algo].nmatches = 0
                viir.__dict__[algo] = HOLDER()
                viir.__dict__[algo].nobs = 0

        # Write matches to file
        for algo in ALGOS:
            mod.__dict__[algo].nymd = nymd
            writeNC(ofile,algo,viir,mod,match,options)

        options.append = False
        nymd += timedelta(hours=1)
