""""
    Generic Evaluation Functionality

    - Refactoring of abc_c6_aux.py
    P. Castellanos, Sep 2024
"""

import os, sys
import matplotlib.pyplot    as      plt
from   matplotlib.ticker    import  MultipleLocator
import matplotlib.patches   as      mpatches
import numpy                as      np
import itertools
from   sklearn.linear_model import LinearRegression
from   glob                 import glob
from   scipy                import stats
from   .nn                  import aodFormat, _cat2
#--------------


class EVAL(object):

    def EvaluationPlots(self,expid,ident,I,nnr2=None,doInt=False):
        """ 
        Creates all the evaluation plots
        nnr2 = another set of obs.  if you want to look at where they overlap. not implemented yet.
        """
        I1, I2, I3, I4 = self.get_Iquartiles(I=[I])
        Ifdu, Ifss, Ifcc, Ifsu, Ifna = self.get_Ispecies(I=[I])

        if self.angstrom_fit:
            self.make_plots = self.make_angstrom_fit_kde_plots 
        elif self.angstrom:
            self.make_plots = self.make_angstrom_kde_plots
        else:
            self.make_plots = self.make_tau_kde_plots

        names = 'q25','q50','q75','q100','fdu','fss','fcc','fsu','fna'
        Is    = I1,I2,I3,I4,Ifdu,Ifss,Ifcc,Ifsu,Ifna
        self.make_plots('AllTest.'+expid,ident,I=I)
        for i,name in zip(Is,names):
            if len(i[0])>0:
                self.make_plots(name+'.'+expid,ident,I=i[0],do2d=False)

    def make_tau_kde_plots(self,expid,ident,I=None,do2d=True):
        """
        create evaluation KDE plots
        this is for the special case that only AOD(s) is predicted
        """
        # make sure output dir exits
        outdir = self.plotdir
        if not os.path.exists(outdir):
            os.makedirs(outdir)

        # if you don't provide indeces, use all data
        if I is None:
            I = np.ones(self.lon.shape).astype(bool)

        # Get the target, original data, and NN predicted data
        targets  = self.getTargets(I,noscale=True)
        if self.nTarget == 1:
            targets.shape = targets.shape + (1,)

        results = self.eval(I,noscale=True)

        original = []
        names = []
        for t in range(self.nTarget):
            name = 'm'+self.Target[t][1:]
            names.append(name[1:])
            # i always want to visualize log(AOD+0.01)
            if name in self.__dict__:
                orig = np.log(self.__dict__[name][I] + 0.01)
            else:
                orig = None

            original.append(orig)

        # i always want to visualize log(AOD+0.01) 
        # because that's what's assimilated
        if not self.laod:
            targets = np.log(targets + 0.01)
            results = np.log(results + 0.01)

        if self.laod and (self.logoffset != 0.01):
            targets = np.log(np.exp(targets) - self.logoffset + 0.01)
            results = np.log(np.exp(results) - self.logoffset + 0.01)


        # plot KDE of new and original Tau
        if do2d:
            self.plot_tau_kde(names,targets,results,original,outdir,expid,ident)
        self.plot_error_pdfs(names,targets,results,original,outdir,expid,ident)

        # If more than one target
        # Plot KDE of Angstrom Exponent
        # Implicitly requires AOD 550
        # -------------------------------
        if self.nTarget > 1:
            names,AEt,AEr,AEo = self.plot_ae_kde(targets,results,original,outdir,expid,ident)
            self.plot_error_pdfs(names,AEt,AEr,AEo,outdir,expid,ident)
#-----
    def make_angstrom_kde_plots(self,expid,ident,I=None,do2d=True):
        """
        create evaluation KDE plots
        this is for the special case that AOD550 and the AE at another channel is predicted
        """
        # make sure output dir exits
        outdir = self.plotdir
        if not os.path.exists(outdir):
            os.makedirs(outdir)

        # if you don't provide indeces, use all data
        if I is None:
            I = np.ones(self.lon.shape).astype(bool)

        # Get the target, original data, and NN predicted data
        targets  = self.getTargets(I,noscale=True)
        if self.nTarget == 1:
            targets.shape = targets.shape + (1,)

        results = self.eval(I,noscale=True)

        # get the basewav tau
        base_wav = self.AE_base_wav
        for t in range(self.nTarget):
            tname = self.Target
            if 'Tau' in tname:
                base_name = tname
                if self.laod:
                    base_tau_t  = np.exp(targets[:,t]) - self.logoffset
                    base_tau_r  = np.exp(results[:,t]) - self.logoffset
                else:
                    base_tau_t = targets[:,t]
                    base_tau_r = results[:,t]               

        # get the Tau's back from the AE
        names = []
        for t in range(self.nTarget):
            tname = self.Target[t]
            if 'AE' in tname:
                wav = float(tname.split('AE')[-1])
                names.append('Tau'+wav)
                tau = base_tau_t*np.exp(-1.*np.log(wav/base_wav)*targets[:,t])
                if self.laod:
                    targets[:,t] = np.log(tau + self.logoffset)
                else:
                    targets[:,t] = tau

                tau = base_tau_r*np.exp(-1.*np.log(wav/base_wav)*results[:,t])
                if self.laod:
                    results[:,t] = np.log(tau + self.logoffset)
                else:
                    results[:,t] = tau
            else:
                names.append(tname[1:])

        # I always want to visualize log(AOD)+0.01
        if not self.laod:
            targets = np.log(targets + 0.01)
            results = np.log(results + 0.01)

        if self.laod and (self.logoffset != 0.01):
            targets = np.log(np.exp(targets) - self.logoffset + 0.01)
            results = np.log(np.exp(results) - self.logoffset + 0.01)

        # get original data
        original = []
        for t in range(self.nTarget):
            name = 'm'+names[t]
            # i always want to visualize log(AOD+0.01)
            if name in self.__dict__:
                orig = np.log(self.__dict__[name][I] + 0.01)
            else:
                orig = None

            original.append(orig)


        # plot KDE of new and original Tau
        if do2d:
            self.plot_tau_kde(names,targets,results,original,outdir,expid,ident)
        self.plot_error_pdfs(names,targets,results,original,outdir,expid,ident)

        # Plot KDE of Angstrom Exponent
        # Implicitly requires AOD 550
        # -------------------------------
        names,AEt,AEr,AEo = self.get_ae550(targets,results,original)
        if do2d:
            self.plot_ae_kde(names,AEt,AEr,AEo,outdir,expid,ident)
        self.plot_error_pdfs(names,AEt,AEr,AEo,outdir,expid,ident)

#-----
    def make_angstrom_fit_kde_plots(self,expid,ident,I=None,do2d=True):
        """
        create evaluation KDE plots
        this is for the special case that AOD550 and the AE multi-spectral angstrom fit
        is predicted
        """
        # make sure output dir exits
        outdir = self.plotdir
        if not os.path.exists(outdir):
            os.makedirs(outdir)

        # if you don't provide indeces, use all data
        if I is None:
            I = np.ones(self.lon.shape).astype(bool)

        # Get the target, original data, and NN predicted data
        targets  = self.getTargets(I,noscale=True)
        if self.nTarget == 1:
            targets.shape = targets.shape + (1,)

        results = self.eval(I,noscale=True)

        # get the AOD from the predicted angstrom
        # linear fit
        # ------------------------------------------------
        AEbt = None
        AEbr = None
        for t in range(self.nTarget):
            tname = self.Target[t]
            if 'AEfitm' in tname:       
                AEmt = targets[:,t]
                AEmr = results[:,t]
            if 'AEfitb' in tname:
                AEbt = targets[:,t]
                AEbr = results[:,t]
            if 'aTau550' in tname:
                tau550t = targets[:,t]
                tau550r = results[:,t]            

        # calculate AEb of prediction
        if AEbr == None:
            AEbr = -1.*(tau550r + AEmr*np.log(550.))


        # wavelengths i want to get tau at
        nwav = 6
        wavs = ['440','470','500','550','660','870']
        wav  = np.array(wavs).astype(float)

        # calculate Tau from AE fits
        nobs, nt = targets.shape
        targets_ = np.zeros([nobs,nwav])
        results_ = np.zeros([nobs,nwav])
        names_   = []
        for i in range(nwav):
            names_.append('Tau'+wavs[i])
            tau = self.__dict__['aTau'+wavs[i]][I]
            targets_[:,i] = np.log(tau + 0.01)  # i always want to visualize log(aod)+0.01
            results_[:,i] = -1.*(AEmr*np.log(wav[i]) + AEbr)  # this is always fit with log(aod)+0.01, so results is already in correct form

        # get original data
        original_ = []
        wavm = []
        for t in range(nwav):
            name = 'mTau'+wavs[t]
            # i always want to visualize log(AOD+0.01)
            if name in self.__dict__:
                orig = np.log(self.__dict__[name][I] + 0.01)
                wavm.append(t)
            else:
                orig = None

            original_.append(orig)


        # plot KDE of new and original Tau
        if do2d:
            self.plot_tau_kde(names_,targets_,results_,original_,outdir,expid,ident)
        self.plot_error_pdfs(names_,targets_,results_,original_,outdir,expid,ident)

        # get AE fit of original data
        mdata = []
        fwav  = []
        for t in wavm:
            name = 'mTau'+wavs[t]
            fwav.append(wav[t])
            mdata.append(self.__dict__[name][I])

        mdata = np.array(mdata)
        fwav  = np.array(fwav)
        fit = np.polyfit(np.log(fwav),-1.*np.log(mdata+0.01),1)
        AEm = fit[0,:]
        AEb = fit[1,:]            

        # Plot KDE of AE fits
        if do2d:
            title = "AE 440-870 " +ident
            # original
            figfile = outdir+"/"+expid+"."+ident+"_kde-AEfitm.png"
            self._plot2dKDE(AEmt,AEm,y_label='Original Retrieval',x_bins=np.arange(-1,3,0.1),title=title,figfile=figfile)

            figfile = outdir+"/"+expid+"."+ident+"_2dhist-AEfitm.png"
            self._plot2dHist(AEmt,AEm,y_label='Original Retrieval',x_bins=np.arange(-1,3,0.1),title=title,figfile=figfile)            
            # corrected
            figfile = outdir+"/"+expid+"."+ident+"_kde-AEfitm-corrected.png"
            self._plot2dKDE(AEmt,AEmr,y_label='NNR',x_bins=np.arange(-1,3,0.1),title=title,figfile=figfile)

            figfile = outdir+"/"+expid+"."+ident+"_2dhist-AEfitm-corrected.png"
            self._plot2dHist(AEmt,AEmr,y_label='NNR',x_bins=np.arange(-1,3,0.1),title=title,figfile=figfile)
            
        
        # error pdf
        AEmt.shape = AEmt.shape + (1,)
        AEmr.shape = AEmr.shape + (1,)
        self.plot_error_pdfs(['AEm'],AEmt,AEmr,[AEm],outdir,expid,ident)

        # if you tried to learn AEb, plot
        if AEbt is not None:
            if do2d:
                title = "AE intercept 440-870 " +ident
                # original
                figfile = outdir+"/"+expid+"."+ident+"_kde-AEfitb.png"
                self._plot2dKDE(AEbt,AEb,y_label='Original Retrieval',x_bins=np.arange(-20,10,0.5),title=title,figfile=figfile)

                figfile = outdir+"/"+expid+"."+ident+"_2dhist-AEfitb.png"
                self._plot2dHist(AEbt,AEb,y_label='Original Retrieval',x_bins=np.arange(-20,10,0.5),title=title,figfile=figfile)                
                # corrected
                figfile = outdir+"/"+expid+"."+ident+"_kde-AEfitb-corrected.png"
                self._plot2dKDE(AEbt,AEbr,y_label='NNR',x_bins=np.arange(-20,10,0.5),title=title,figfile=figfile)

                figfile = outdir+"/"+expid+"."+ident+"_2dhist-AEfitb-corrected.png"
                self._plot2dHist(AEbt,AEbr,y_label='NNR',x_bins=np.arange(-20,10,0.5),title=title,figfile=figfile)
                

            # error pdf
            AEbt.shape = AEbt.shape + (1,)
            AEbr.shape = AEbr.shape + (1,)
            self.plot_error_pdfs(['AEb'],AEbt,AEbr,[AEb],outdir,expid,ident)

#------
    def plot_error_pdfs(self,names,targets,results,original,outdir,expid,ident):
        """
        create probability density functions plots of error
        generic wrapper for _plot1dKDE
        """
        # calculate rmse
        nnrRMSE = self.rmse(results,targets)
        nnrME   = self.me(results,targets)
        for t,name in enumerate(names):
            orig = original[t]
            tar  = targets[:,t]
            if orig is not None:
                origRMSE = self.rmse(orig,tar)
                origME   = self.me(orig,tar)
                label2 = 'Standard RMSE={:1.2F}, ME={:1.2F}'.format(origRMSE,origME)
                values2 = orig - tar
            else:
                label2 = None
                values2 = None

            figfile = outdir+"/"+expid+"."+ident+"_error_pdf-"+name+'.png'
            title   = "Error " + name
            label   = 'NNR RMSE={:1.2F}, ME={:1.2F}'.format(nnrRMSE[t],nnrME[t])
            values  = results[:,t] - tar
            self._plot1dKDE(values,label,values2=values2,label2=label2,figfile=figfile,title=title)

#------
    def plot_tau_kde(self,names,targets,results,original,outdir,expid,ident):
        """
        Generic wrapper for _plot2dKDE
        """
        nobs, nTarget = targets.shape
        # plot KDE of new predictions
        for t in range(nTarget):
            figfile = outdir+"/"+expid+"."+ident+"_kde-"+names[t]+'-corrected.png'
            title = "Log("+names[t]+"+0.01)- "+ident
            self._plot2dKDE(targets[:,t],results[:,t],y_label='NNR',figfile=figfile,title=title)

            figfile = outdir+"/"+expid+"."+ident+"_2dhist-"+names[t]+'-corrected.png'
            self._plot2dHist(targets[:,t],results[:,t],y_label='NNR',figfile=figfile,title=title)


        # Plot KDE of uncorrected AOD
        # loop through targets
        # plot if there's a corresponding MODIS retrieval
        for t in range(nTarget):
            if original[t] is not None:
                title = "Log("+names[t]+"+0.01)- "+ident
                figfile = outdir+"/"+expid+"."+ident+"_kde-"+names[t]+'.png'
                self._plot2dKDE(targets[:,t],original[t],y_label='Original Retrieval',figfile=figfile,title=title)

                figfile = outdir+"/"+expid+"."+ident+"_2dhist-"+names[t]+'.png'
                self._plot2dHist(targets[:,t],original[t],y_label='Original Retrieval',figfile=figfile,title=title)

                # Scatter diagram for testing
                # ---------------------------
                figfile = outdir+"/"+expid+"."+ident+"_scat-"+names[t]+'.png'
                self._plotScat(targets[:,t],original[t],y_values2=results[:,t],
                               y_label='Satellite',figfile=figfile,
                               label='Original',label2='Corrected')

#------
    def get_ae550(self,targets,results,original):
        """
        generic calculation of AE with respect to 550 
        implicitly requires 550 nm AOD
        """
        # AE from Corrected AOD
        # ----------------------
        refname = 'Tau550'
        refwav  = 550.

        # get reference wavelength Tau
        for t in range(self.nTarget):
            name = self.Target[t][1:]
            if name == refname:
                reft = np.exp(targets[:,t])  # keep the + 0.01 to handle negatives in MODIS data
                refr = np.exp(results[:,t])  # keep the + 0.01 to handle negatives in MODIS data
                refo = np.exp(original[t])

        # calculate AE with respect to 550
        names,AEt_,AEr_,AEo_ = [],[],[],[]
        for t in range(self.nTarget):
            name = self.Target[t][1:]
            if name != refname:
                print('t,wav',t,name[3:])
                wav = float(name[3:])
                tt = np.exp(targets[:,t])  # keep the + 0.01 to handle negatives in MODIS data
                rr = np.exp(results[:,t])  # keep the + 0.01 to handle negatives in MODIS data
                AEt = -1.*np.log(reft/tt)/np.log(refwav/wav)
                AEr = -1.*np.log(refr/rr)/np.log(refwav/wav)

                AEt_.append(AEt)
                AEr_.append(AEr)
    
                names.append(name[3:])

                if orginial[t] is not None:
                    oo = np.exp(original[t]) # keep the + 0.01 to handle negatives in MODIS data
                    AEo = -1.*np.log(refo/oo)/np.log(refwav/wav)
                    AEo_.append(AEo)
                else:
                    AEo_.append(None)

        return names,AEt_,AEr_,AEo_
#                
#------
    def plot_ae_kde(self,names,AEt,AEr,AEo,outdir,expid,ident):
        """
        generic wrapper to create AE with respect to 550 AOD KDE plots
        """
        bins = np.arange(0., 3., 0.05 )

        # plot AE with respect to 550
        for t,name in enumeate(names):

                AEt_ = AEt[t]
                AEr_ = AEr[t]

                title = "AE 550/"+name
                figfile = outdir+"/"+expid+"."+ident+"_kde-AE"+name+'-corrected.png'
                self._plot2dKDE(AEt_,AEr_,y_label='NNR',x_bins=bins,y_bins=bins,title=title,figfile=figfile)

                figfile = outdir+"/"+expid+"."+ident+"_2dhist-AE"+name+'-corrected.png'
                self._plot2dHist(AEt_,AEr_,y_label='NNR',x_bins=bins,y_bins=bins,title=title,figfile=figfile)

                if AEo[t] is not None:
                    figfile = outdir+"/"+expid+"."+ident+"_kde-AE"+name+'.png'
                    self._plot2dKDE(AEt_,AEo[t],y_label='Standard',x_bins=bins,y_bins=bins,title=title,figfile=figfile)

                    figfile = outdir+"/"+expid+"."+ident+"_2dhist-AE"+name+'.png'
                    self._plot2dHist(AEt_,AEo[t],y_label='Standard',x_bins=bins,y_bins=bins,title=title,figfile=figfile)

#------
    def _plot1dKDE(self,values,label,values2=None,label2=None,nbins=100,x_label='Difference',figfile=None,title=None):
        """
        Plot a KDE estimate of the probability density function
        """
        emax = values.max()
        emin = values.min()
        if values2 is not None:
            emax = max([emax,values2.max()])

        xcen = np.linspace(emin,emax,nbins+1)
        # get kde
        kernel = stats.gaussian_kde(values)
        data = kernel(xcen)

        if values2 is not None:
            kernel = stats.gaussian_kde(values2)
            data2 = kernel(xcen)

        fig = plt.figure()
        ax = fig.add_axes([0.1,0.1,0.75,0.75]) 
        ax.plot(xcen,data,label=label,color='r')
        if values2 is not None:
            ax.plot(xcen,data2,label=label2,color='k')

        ax.legend()
        ax.grid(color='0.50',linestyle='-')

        if title is not None:
            ax.set_title(title)

        if figfile is not None:
            plt.savefig(figfile)
            plt.close(fig)
        else:
            plt.show()
#------
    def _plot2dKDE(self,x_values,y_values,x_bins=None,y_bins=None,
                 x_label='AERONET', y_label='STANDARD',figfile=None,title=None):
        """
        Plot Target vs Model using a 2D Kernel Density Estimate.
        """

        if x_bins is None: x_bins = np.arange(-5., 1., 0.1 )
        if y_bins is None: y_bins = x_bins

        Nx = len(x_bins)
        Ny = len(y_bins)

        print("Evaluating 2D kernel on grid with (Nx,Ny)=(%d,%d) ..."%(Nx,Ny))
        kernel = stats.kde.gaussian_kde(self._cat2(x_values,y_values))
        X, Y = np.meshgrid(x_bins,y_bins)   # each has shape (Ny,Nx)
        Z = kernel(_cat2(X,Y))           # shape is (Ny*Nx)
        Z = np.reshape(Z,X.shape)

        if self.laod:
            formatter = aodFormat()
        else:
            formatter = None

        fig = plt.figure()
        ax = fig.add_axes([0.1,0.1,0.75,0.75])
        if formatter != None:
            ax.xaxis.set_major_formatter(formatter)
            ax.yaxis.set_major_formatter(formatter)
        ax.imshow(Z, cmap=plt.cm.gist_earth_r, origin='lower',
               extent=(x_bins[0],x_bins[-1],y_bins[0],y_bins[-1]) )
        ax.plot([x_bins[0],x_bins[-1]],[y_bins[0],y_bins[-1]],'k')
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        ax.grid()
        if title is not None:
            ax.set_title(title)

        if figfile is not None:
            plt.savefig(figfile)
            plt.close(fig)
        else:
            plt.show()

#------
    def _plot2dHist(self,x_values,y_values,x_bins=None,
                 x_label='AERONET', y_label='STANDARD',figfile=None,title=None):
        """
        Plot Target vs Model using a 2D Historgram
        """

        if x_bins is None: x_bins = np.arange(-5., 1., 0.1 )

        if self.laod:
            formatter = aodFormat()
        else:
            formatter = None

        fig = plt.figure()
        ax = fig.add_axes([0.1,0.1,0.75,0.75])
        if formatter != None:
            ax.xaxis.set_major_formatter(formatter)
            ax.yaxis.set_major_formatter(formatter)
        ax.hist2d(x_values,y_values,bins=x_bins,cmap=plt.cm.gist_earth_r)
        ax.plot([x_bins[0],x_bins[-1]],[x_bins[0],x_bins[-1]],'k')
        ax.set_xlim([x_bins[0],x_bins[-1]])
        ax.set_ylim([x_bins[0],x_bins[-1]])
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        ax.grid()
        if title is not None:
            ax.set_title(title)

        if figfile is not None:
            plt.savefig(figfile)
            plt.close(fig)
        else:
            plt.show()
#-----
    def _plotScat(self,x_values,y_values,y_values2=None,
                  x_label='AERONET', y_label='STANDARD',label=None,label2=None,
                  figfile=None,title=None,):
        """
        Plot Target vs Model as a scatter plot
        """
        vmin = min([x_values.min(),y_values.min()])
        vmax = max([x_values.max(),y_values.max()])
        if y_values2 is not None:
            vmin = min([vmin,y_values2.min()])
            vmax = max([vmax,y_values.max()])

        fig = plt.figure()
        ax = fig.add_axes([0.1,0.1,0.75,0.75])
        ax.plot(x_values,y_values,'ko',label=label)
        if y_values2 is not None:
            ax.plot(x_values,y_values2,'bo',alpha=0.5,label=label2)
        ax.plot([vmin,vmax],[vmin,vmax],'k')
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        ax.grid()
        ax.legend()
        if title is not None:
            ax.set_title(title)

        if figfile is not None:
            plt.savefig(figfile)
            plt.close(fig)
        else:
            plt.show()        

#-----
    def _cat2 (self,X, Y):
        """
        Given 2 arrays of same shape, returns array of shape (2,N),
        where N = X.size = Y.size
        """
        xy = np.concatenate((X.ravel(),Y.ravel())) # shape is (N+N)
        return np.reshape(xy,(2,X.size))         # shape is (2,N)

# ---
    def rmse(self,predictions, targets):
        return np.sqrt((np.square(predictions - targets)).mean(axis=0))
# ---
    def mae(self,predictions, targets):
        return np.abs(predictions-targets).mean(axis=0)
# ---
    def me(self,predictions, targets):
        return (predictions-targets).mean(axis=0)   
# ---
    def get_Iquartiles(self,I=None,var=None):

        Irange     = np.arange(self.nobs)
        if I is None:
            I          = [Irange[self.iValid]]

        I1 = []
        I2 = []
        I3 = []
        I4 = []
        for iTest in I:
            if var is None:
                targets  = self.getTargets(iTest,noscale=True)
            else:
                targets = self.__dict__[var][iTest].squeeze()
            if len(targets.shape) > 1:
                targets = targets[:,0]

            p25  = np.percentile(targets,25)
            p50  = np.percentile(targets,50)
            p75  = np.percentile(targets,75)
            p100 = targets.max()

            I1.append(Irange[iTest][targets <= p25])
            I2.append(Irange[iTest][(targets>p25) & (targets<=p50)])
            I3.append(Irange[iTest][(targets>p50) & (targets<=p75)])
            I4.append(Irange[iTest][(targets>p75)])

        return I1, I2, I3, I4
# ---
    def get_Ispecies(self,I=None):

        Irange     = np.arange(self.nobs)
        if I is None:
            I          = [Irange[self.iValid]]

        Ifdu = []
        Ifss = []
        Ifcc = []
        Ifsu = []
        Ifna = []
        for iTest in I:
            fdu  = self.fdu[iTest].squeeze()
            fss  = self.fss[iTest].squeeze()
            fcc  = self.fcc[iTest].squeeze()
            fsu  = self.fsu[iTest].squeeze()

            Ifdu.append(Irange[iTest][fdu >= 0.5])
            Ifss.append(Irange[iTest][fss >= 0.5])
            Ifcc.append(Irange[iTest][fcc >= 0.5])
            Ifsu.append(Irange[iTest][fsu >= 0.5])
            Ifna.append(Irange[iTest][(fdu<0.5) & (fss<0.5) & (fcc<0.5) & (fsu<0.5)])
        return Ifdu, Ifss, Ifcc, Ifsu, Ifna
