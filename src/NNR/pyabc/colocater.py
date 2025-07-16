"""
    Subroutines to do obs co-location
"""

import numpy as np
from   datetime import timedelta
from   binObs_   import binobs2d, binobs3d, binobscnt3d

def haversine(lat1, lon1, lat2, lon2):
        """
        Calculate the great circle distance between two points
        on the earth (specified in decimal degrees)

        lat1, lon1, lat2, lon2 are arrays
        """
        # convert decimal degrees to radians
        lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])

        # haversine formula
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
        c = 2 * np.arcsin(np.sqrt(a))
        r = 6371 # Radius of earth in kilometers. Use 3956 for miles
        return c * r  

class station_swath(object):
    """
    Returns lists of station obs indices and satellite obs indices that are colocated
    Assumes satellite overpasses station once
    Satellite obs should fall within a radius of Dx km from the station
    Station obs should occur within +/Dt minutes of satellite overpass

    station object must have the following attributes:
        Location
        lon
        lat
        tyme
        nobs

    swath object must have the following attributes:
        lon
        lat
        tyme
        nobs
    """

    def __init__(self,station,swath,Dt=30,Dx=27.5):
        self.Dt = timedelta(minutes=Dt)
        self.Dx = Dx

        self.usites = np.unique(station.Location)
        self.coarseColocate(station,swath)
        self.fineColocate(station,swath)


    def coarseColocate(self,station,swath):
        # For each unique station site
        # Loop through and look for possible distance & time matches
        # Coarse initial search

        dtMax = self.Dt*2
        dlMax = self.Dx*2/100  #roughly degrees
        self.Cmatches = []

        for site in self.usites:
            isite = station.Location == site
            lon,lat = station.lon[isite][0], station.lat[isite][0]

            # Does satellite observe near the stations?
            distfound = (np.abs(lon - swath.lon) < dlMax) & (np.abs(lat - swath.lat) < dlMax)

            # Do the stations have data when the satellite overpasses?
            times = station.tyme[isite]
            timefound = np.zeros(times.shape)
            for i,t in enumerate(times):
                tmin = t - dtMax
                tmax = t + dtMax

                #print 'tmax',tmax
                #print 'tmin',tmin
                #print 'tyme',swath.tyme[distfound]
                #print 'distfound',np.arange(len(distfound))[distfound]
                timefound[i] = np.any((swath.tyme[distfound] <= tmax) & (swath.tyme[distfound] >= tmin))

            if np.any(timefound) & np.any(distfound):
                self.Cmatches.append(np.arange(swath.nobs)[distfound])
            else:
                self.Cmatches.append([])



    def fineColocate(self,station,swath):
        # For each station site that has coarse matches
        # loops thrgh and looks for distance and time matches

        dtMax = self.Dt
        dlMax = self.Dx #km
        self.swathMatches = []
        self.stationMatches = []
        self.distance = []
        self.nmatches = 0

        
        for site,mm in zip(self.usites,self.Cmatches):
            if any(mm):
                isite = station.Location == site

                # Get satellite obs within a dlMax circle of station site
                alat,alon = station.lat[isite][0],station.lon[isite][0]
                mlat,mlon = swath.lat[mm], swath.lon[mm]
                distance = haversine(alat,alon,mlat,mlon)

                found = distance <= dlMax
                
                if not any(found):
                    self.stationMatches.append([])
                    self.swathMatches.append([])
                    self.distance.append([])
                else:
                    
                    # Get station obs within +/- dtMax of median swath overpass
                    atyme = station.tyme[isite]
                    mdT   = (swath.tyme[mm[found]].max() - swath.tyme[mm[found]].min()).total_seconds()
                    mtyme = swath.tyme[mm[found]].min() + timedelta(seconds=mdT*0.5)

                    tmin = mtyme - dtMax
                    tmax = mtyme + dtMax
                    tfound = (atyme <= tmax) & (atyme >= tmin)

                    if any(found) & any(tfound):
                        self.swathMatches.append(mm[found])
                        self.distance.append(distance[found])
                        self.stationMatches.append(np.arange(station.nobs)[isite][tfound])
                        self.nmatches += 1
                    else:
                        self.stationMatches.append([])
                        self.swathMatches.append([])
                        self.distance.append([])

            else:
                self.swathMatches.append([])
                self.stationMatches.append([])
                self.distance.append([])


# -----------------------------------------------------------------------------
class swath_geo(object):
    """
    Returns lists of LEO satellite indices and GEO satellite indices that are colocated
    GEO pixel centers should fall within a radius of Dx km from the LEO pixel center
    LEO obs should occur within +/Dt minutes of GEO time - assume only one GEO obs per pixel

    swath & geo objects must have the following attributes:
        lon
        lat
        tyme
        nobs

    geo must have time attribute
    """

    def __init__(self,swath,geo,Dt=15,Dx=5):
        self.Dt = timedelta(minutes=Dt)
        self.Dx = Dx


        self.coarseColocate(swath,geo)
        self.fineColocate(swath,geo)


    def coarseColocate(self,swath,geo):
        # Coarse initial search
        


        # find min/max latlon of leo swath
        # limit search for coarse matches to 
        # geo pixels in a box containing leo swath
        dtMax = self.Dt
        dlMax = self.Dx*2./100.  #roughly degrees

        minlon, maxlon = swath.lon.min()-dlMax, swath.lon.max()+dlMax
        minlat, maxlat = swath.lat.min()-dlMax, swath.lat.max()+dlMax
        #mintyme, maxtyme = geo.time-dtMax, geo.time+dtMax
        mintyme, maxtyme = geo.tyme.min()-timedelta(minutes=5), geo.tyme.max()+timedelta(minutes=5)

        #print 'minlon,maxlon',minlon,maxlon
        #print 'minlat,maxlat',minlat,maxlat

        dGood = (geo.lon >= minlon) & (geo.lon <= maxlon) & (geo.lat >= minlat) & (geo.lat <= maxlat)
        tGood = (swath.tyme >= mintyme) & (swath.tyme <= maxtyme)

        self.Cgeomatches = []
        self.Cleomatches = []
        if np.any(dGood) & np.any(tGood):
            tGoodi = np.arange(swath.nobs)[tGood]
            for i in tGoodi:
                lon = swath.lon[i]
                lat = swath.lat[i]
                
                
                # Does geo observe near this swath pixel?
                found = (np.abs(lon - geo.lon) < dlMax) & (np.abs(lat - geo.lat) < dlMax) 

                if np.any(found):
                    self.Cgeomatches.append(np.arange(geo.nobs)[found])
                    self.Cleomatches.append(i)



    def fineColocate(self,swath,geo):
        # For each swath pixel that has coarse matches
        # loops thrgh and looks for distance and time matches

        dlMax = self.Dx #km
        self.leoMatches = []
        self.geoMatches = []
        self.distance = []
        self.nmatches = 0

        
        for lm,gm in zip(self.Cleomatches,self.Cgeomatches):

            # Get geo obs within a dlMax circle of station site
            slat,slon = swath.lat[lm],swath.lon[lm]
            glat,glon = geo.lat[gm], geo.lon[gm]
            distance = haversine(slat,slon,glat,glon)

            found = distance <= dlMax
            
            if any(found):                
                self.leoMatches.append(lm)
                self.distance.append(distance[found])
                self.geoMatches.append(gm[found])
                self.nmatches += 1



# -----------------------------------------------------------------------------

class ods_swath(object):
    """
    Returns lists of LEO satellite indices that are colocated
    Using binObs to grid each on a grid with im lats and jm lons
    Obs should occur within +/Dt minutes of each other

    swath & ods objects must have the following attributes:
        lon
        lat
        DT
        nobs

    """
    def __init__(self,ods,swath,Dt=30):
        self.Dt = Dt

        self.coarseColocate(ods,swath)

    def coarseColocate(self,ods,swath):
        MISSING = 999.999
        # grid times
        otime = binobs2d(ods.lon,ods.lat,ods.DT,ods.im,ods.jm,MISSING)

        lon = np.linspace(-180.,180.,ods.im,endpoint=False)
        lat = np.linspace(-90.,90.,ods.jm)       
        glat,glon = np.meshgrid(lat,lon)

        I = otime != MISSING
        otime = otime[I]
        glon = glon[I]
        glat = glat[I]
        iGood = np.arange(ods.im*ods.jm)[I.ravel()]
        nods = len(glat)


        dtMax = self.Dt*2
        dlMax = 0.5*360./ods.im 
        self.swathMatches = []
        self.odsMatches = []

        for iods in np.arange(nods):
            lon,lat,time,igood = glon[iods],glat[iods],otime[iods],iGood[iods]
            
            # Does satellite observe near the stations?
            found = (np.abs(lon - swath.lon) < dlMax) & (np.abs(lat - swath.lat) < dlMax) & (np.abs(time - swath.DT) < dtMax)

            if np.any(found):
                self.swathMatches.append(np.arange(swath.nobs)[found])
                self.odsMatches.append([igood])


        self.nmatches = len(self.odsMatches)

