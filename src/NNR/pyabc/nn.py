"""
   Generic Neural Net Functionality.

   Arlindo da Silva, June 2015.

"""

import os, sys
from . import sknet as nn

from   matplotlib.pyplot import  cm, imshow, plot, figure
from   matplotlib.pyplot import  xlabel, ylabel, title, grid, savefig, legend
from   numpy             import  c_ as cat
from   numpy             import  random, sort, pi, load, cos, log, std, exp
from   numpy             import  reshape, arange, ones, zeros, interp
from   numpy             import  meshgrid, concatenate, mgrid
import numpy             as      np
from   matplotlib        import  ticker
from   scipy             import  stats, optimize
from   sklearn.model_selection import KFold
from   .error_funcs      import rmse, mae, me
#..............................................................
class aodFormat(ticker.Formatter):
    def __call__(self,x,pos=None):
        y = exp(x)-0.01
        return '%4.2f'%y
#..............................................................

class NN(object):

    def train_tnc_aeroml(self, input, target, nproc = 1, **kwargs):
        """
        :Parameters:
            input : 2-D array
                Array of input patterns
            target : 2-D array
                Array of network targets
            nproc : int or 'ncpu', optional
                Number of processes spawned for training. If nproc='ncpu'
                nproc will be set to number of avilable processors
            maxfun : int
                Maximum number of function evaluation. If None, maxfun is
                set to max(100, 10*len(weights)). Defaults to None.
            bounds : list, optional
                *(min, max)* pairs for each connection weight, defining
                the bounds on that weight. Use None for one of *min* or
                *max* when there is no bound in that direction.
                By default all bounds ar set to (-100, 100)
            messages : int, optional
                If 0, then no output (default). If positive number then
                convergence messages are dispalyed.

        :Returns:
            rc: fmin_tnc return code
            Return codes are defined as follows:

            -1 : Infeasible (lower bound > upper bound)
            0 : Local minimum reached (|pg| ~=0) 
            1 : Converged (|fn - fn-1| ~=0)
            2 : Converged (|xn - xn-1| ~=0)
            3 : Max. number of function evaluations reached
            4 : Linear search failed
            5 : All lower bounds are equal to the upper bounds
            6 : Unable to progress
            7 : User requested end of minimization

        .. note::
            On Windows using *ncpu > 1* might be memory hungry, because
            each process have to load its own instance of network and
            training data. This is not the case on Linux platforms.

        .. seealso::
            `scipy.optimize.fmin_tnc` optimizer is used in this method. Look
            at its documentation for possible other useful parameters.
        """
        from ffnet.fortran import _ffnet as netprop

        input, target = self.net._setnorm(input, target)
        if 'messages' not in kwargs: kwargs['messages'] = 0
        if 'bounds' not in kwargs: kwargs['bounds'] = ((-100., 100.),)*len(self.net.conec)

        # multiprocessing version if nproc > 1
        if (isinstance(nproc, int) and nproc > 1) or nproc in (None, 'ncpu'):
            if nproc == 'ncpu': nproc = None
            rc = self._train_tnc_mp_aeroml(input, target, nproc = nproc, **kwargs)
            return rc # return code for fmin_tnc

        # single process version
        func = netprop.func2  # returns both function and gradient
        extra_args = (self.net.conec, self.net.bconecno, self.net.units, \
                           self.net.inno, self.net.outno, input, target)
        res = optimize.fmin_tnc(func, self.net.weights, \
                                         args=extra_args, **kwargs)
        self.net.weights = np.array( res[0] )
        self.net.trained = 'tnc'

        return res[2]   # return code for fmin_tnc

    def _train_tnc_mp_aeroml(self, input, target, nproc = None, **kwargs):
        """
        Parallel training with TNC algorithm

        Standard multiprocessing package is used here.
        """
        #register training data at mpprop module level
        # this have to be done *BEFORE* creating pool
        from ffnet import _mpprop as mpprop
        try: key = max(mpprop.nets) + 1
        except ValueError: key = 0  # uniqe identifier for this training
        mpprop.nets[key] = self.net
        mpprop.inputs[key] = input
        mpprop.targets[key] = target

        # create processing pool
        from multiprocessing import Pool, cpu_count
        if nproc is None: nproc = cpu_count()
        if sys.platform.startswith('win'):
            # we have to initialize processes in pool on Windows, because
            # each process reimports mpprop thus the registering
            # made above is not enough
            # WARNING: this might be slow and memory hungry
            # (no shared memory, all is serialized and copied)
            initargs = [key, self, input, target]
            pool = Pool(nproc, initializer = mpprop.initializer, initargs=initargs)
        else:
            pool = Pool(nproc)
        
        # save references for later cleaning
        self.net._mppool = pool
        self.net._mpprop = mpprop
        self.net._mpkey = key
        
        # generate splitters for training data
        splitters = mpprop.splitdata(len(input), nproc)

        # train
        func = mpprop.mpfunc2

        #if 'messages' not in kwargs: kwargs['messages'] = 0
        #if 'bounds' not in kwargs: kwargs['bounds'] = ((-100., 100.),)*len(self.conec)
        res = optimize.fmin_tnc(func, self.net.weights, \
                                args = (pool, splitters, key), **kwargs)
        self.net.weights = res[0]

        # clean mpprop and pool
        self.net._clean_mp()

        return res[2]   # return code for fmin_tnc



    def train (self,Input=None,Target=None,nHidden=200,maxfun=1,biases=True,
               topology=None,bounds=[-100,100],newnet=True,netFile=None, **kwargs):
        """
        Train the Neural Net, using a maximum of *maxfun* iterations.
        On input,
            Input   ---  string list with the name of the predictors;
                         if specified dataset specific default is
                         redefined.
            Target  ---  string list with the name of the targets;
                         if specified dataset specific default is
                         redefined.
           nHidden  ---  number of hidden nodes
           maxfun   ---  max number of iterations
           biases   ---  whether to include bias nodes
           newnet   ---  start a new NN or use an existing one
           netFile  ---  in the case of newnet, netFile to be read in
         topology   ---  Network topology; default is (nInput,nHidden,nTarget)
         
         Returns:
            Nothing.
        """
            
        # Possibly redefine Input/Targets
        # -------------------------------
        if Input != None:
            self.Input = Input
        if Target != None:
            self.Target = Target

        # Instantiate Neural Net
        # ----------------------
        if topology==None:
            topology = (len(self.Input), nHidden,len(self.Target))
        #self.net = nn.ffnet(nn.mlgraph(topology,biases=biases))
        if newnet:
            self.net = nn.SKNET(nn.mlgraph(topology,biases=biases))
            ermse, emae, eme, esqerr = [],[],[],[]
            e0 = 0
        else:
            self.net = nn.loadnet(netFile)
            self.net.trained = 'tnc'
            ermse, emae, eme, esqerr = self.ermse, self.emae, self.eme, self.esqerr
            e0 = len(ermse)

        # Add these attributes to net so that later on
        # we now how to apply it to regular MODIS data
        # --------------------------------------------
        self.net.InputNames = self.Input
        self.net.TargetNames = self.Target
        self.net.laod = self.laod
        self.net.logoffset = self.logoffset
        if self.surface == 'ocean':
            self.net.Wind = self.Wind

        self.net.scale = self.scale
        if self.scale:
            self.net.scaler = self.scaler

        self.net.lInput_nnr = self.lInput_nnr
        if self.lInput_nnr is not None:
            for vname in self.lInput_nnr:
                self.net.__dict__['scaler_l'+vname] = self.__dict__['scaler_l'+vname]


        # Indices for training set
        # ------------------------
        try:
            iTrain = self.iTrain
        except AttributeError:
            iTrain = self.iValid # good QC marks


        # Increase the weighting of near zero AOD550 values in training
        # -------------------------------------------------------
        if self.near_zero_weight_epsilon:
            targets = self.getTargets(iTrain)
            print(f"Oversampling values less than {self.near_zero_weight_epsilon}")
            print("array shape",targets.shape,"number of targets",len(Target))
            for i,tname in enumerate(Target):
                if 'Tau550' in tname:
                    if len(Target) == 1:
                        targ = targets
                    else:
                        targ = targets[:,i]
                    # near zero weight ~ 5, far from zero weight ~1
                    w = 1.0 + 4.0*np.exp(-(targ/self.near_zero_weight_epsilon)**2)
                    # normalize to probabilities
                    p = w/w.sum()
                    N = len(targ)
                    M = 3*N  #oversample high weights by 3
                    idx = np.random.choice(N,size=M,replace=True,p=p)
                    if iTrain.dtype == bool:
                        iTrain = np.arange(len(iTrain))[iTrain][idx]
                    else:
                        iTrain = iTrain[idx]

        if self.exp_weight_percentile:
            inputs = self.getInputs(iTrain)
            print(f"Oversampling top {self.exp_weight_percentile} percentile cases")
            for i,iname in enumerage(Input):
                if 'ref550' in iname:
                    inp = inputs[:,i]

                    # exponential/solf-threshold weighting
                    y_ref = np.percentile(inp,100-self.exp_weight_percentile)
                    alpha = 4.0 # strength of scaling
                    w = 1.0 + alpha*np.exp(inp/y_ref)
                    p = w/w.sum()
                    N = len(inp)
                    M = 3*N #oversample high weights by 3
                    idx = np.random.choice(N,size=M,replace=True,p=p)
                    if iTrain.dtype == bool:
                        iTrain = np.arange(len(iTrain))[iTrain][idx]
                    else:
                        iTrain = iTrain[idx]                    


        # Prepare inputs and targets
        # --------------------------
        inputs  = self.getInputs(iTrain)
        targets = self.getTargets(iTrain) 


        # Indices for testing set
        # ------------------------
        try:
            iTest = self.iTest
        except AttributeError:
            iTest = self.iValid

        # Prepare inputs and targets
        # --------------------------
        test_inputs  = self.getInputs(iTest)
        test_targets = self.getTargets(iTest)
        test1_targets = test_targets
        if self.nTarget == 1:
            test1_targets.shape = test1_targets.shape + (1,)

        # Train
        # -----
#        bounds = [-1000,1000]
#        maxfun = 10000
#        maxfun = 50000
        bounds = [bounds]*self.net.conec.shape[0]
        if self.verbose>0:
            print("Starting training with %s inputs and %s targets"\
                  %(str(inputs.shape),str(targets.shape)))

#        nfun = 10*len(self.net.weights)
        nfun = 2550
        for e in range(0,maxfun):
            epoch = e0 + e
            print('epoch',epoch,'epoch cnt',e,'nepoch',maxfun,'nfun',nfun)
            rc = self.train_tnc_aeroml(inputs,targets, maxfun=nfun,bounds=bounds,**kwargs)
            esqerr.append(self.net.sqerror(inputs,targets))

            # len(regression) = nTarget
            # regression[*][0:2] = slope, intercept, r-value
            # out.shape = [ntestobs,nTarget]
            # ------------------------
            output, reg = self.net.test(test_inputs,test_targets,iprint=False)

            # get other NNR STATS
            ermse.append(rmse(output,test1_targets))
            emae.append(mae(output,test1_targets))
            eme.append(me(output,test1_targets))
            enetFile = f"{netFile[:-4]}.{int(epoch):03d}.net"
            self.savenet(enetFile)

            if rc != 3:
                print('fmin_tnc return code ',rc)
                break # Exit for loop

#        self.net.train_tnc(inputs,targets, maxfun=maxfun,bounds=bounds,**kwargs)
#        self.net.train_bfgs(inputs,targets, maxfun=maxfun)
        self.ermse = ermse
        self.emae  = emae
        self.eme   = eme
        self.esqerr = esqerr

    def test(self,iprint=1,fname=None):

        # Indices for training set
        # ------------------------
        try:
            iTest = self.iTest
        except AttributeError:
            iTest = self.iValid
            
        # Prepare inputs and targets
        # --------------------------
        inputs  = self.getInputs(iTest)
        targets = self.getTargets(iTest) 

        return self.net.test(inputs,targets,iprint=iprint,filename=fname)
        
    def eval(self,I=None,noscale=False):
        if I is None: I = self.iValid
        inputs = self.getInputs(I)
        results = self.net(inputs)
        if self.scale:
            if noscale:
                results = self.scaler.inverse_transform(results)
        return results

    __call__ = eval

    def derivative(self,I=None):
        if I is None: I = self.iValid
        return self.net.derivative(self.getInputs(I))
    
    def savenet(self,fname):
        nn.savenet(self.net,fname)

    def loadnet(self,fname):
        return nn.loadnet(fname)    

    def exportnet(self,fname):
        nn.exportnet(self.net,fname)
        
    def split (self,fTrain=0.9):
        """
        Splits the input dataset in training and testing subsets. No data is
        actually moved only attributes with indices iTrain/iTest are created;
        only data with an iValid Q/C flag is considered. On input, *fTrain* is
        the fraction of the dataset to be used for training.
        Returns: (nothing)
        """
        n = self.lon.size
        nTrain = int(fTrain * n)
        random.seed(32768) # so that we get the same permutation
        i = random.permutation(n)
        iValid = self.iValid[i]
        self.iTrain = i[0:nTrain][iValid[0:nTrain]] # Keep only good obs
        self.iTest  = i[nTrain:][iValid[nTrain:]]   # Keep only good obs

    def kfold(self,K=3):
        """
        Splits input dataset into K training and testing subsets.
        Only data with an iValid Q/C flag is considered.
        """
        self.kf = KFold(n_splits=K, shuffle=True, random_state=self.nobs)


    def getInputs(self,I,Input=None):
        """
        Given a set of indices *I*, returns the corresponding
        inputs for a neural net evaluation.
        Returns: inputs
        """
        if self.verbose:
            print(" ")
            print("       Feature          Min      Max")
            print("  ------------------  -------  -------")
        if Input==None:
            Input = self.Input
        inputs = self.__dict__[Input[0]][I]
        if self.verbose:
            print("%20s %8.4f %8.4f"%(Input[0],inputs.min(),inputs.max()))
        for var in Input[1:]:
            q = self.__dict__[var][I]
            inputs = cat[inputs,q]
            if self.verbose:
                print("%20s %8.4f %8.4f"%(var,q.min(),q.max()))
        if self.verbose:
            print("  ------------------  -------  -------")
            print("")

        if len(inputs.shape) == 1:
            inputs.shape = (inputs.shape[0],1)            
        return inputs
    
    def getTargets(self,I,noscale=False):
        """
        Given a set of indices *I*, return the corresponding
        targets for a neural net evaluation:
        Returns: tagets
        """
        var = self.Target[0]
        if self.laod and ('Tau' in var):
            targets = log(self.__dict__[var][I] + self.logoffset)
        else:
            targets = self.__dict__[var][I]

        for var in self.Target[1:]:
            if self.laod and ('Tau' in var):
                targets = cat[targets,log(self.__dict__[var][I] + self.logoffset)]
            else:
                targets = cat[targets,self.__dict__[var][I]]

        if self.scaler is not None:
            if not noscale:
                if self.nTarget == 1:
                    targets = self.scaler.transform(targets.reshape(-1,1)).squeeze()
                else:
                    targets = self.scaler.transform(targets)

        return targets
 
    def plotKDE(self,bins=None,I=None,figfile=None,
                x_label='AERONET'):
        """
        Plot Target vs Model using a 2D Kernel Density Estime.
        """
        if I is None: I = self.iValid # All data by default
        results = self.eval(I)
        targets = self.getTargets(I)
        if self.scale:
            targets = self.scaler.inverse_transform(targets)
        if self.laod:
            formatter = aodFormat(self.logoffset)
        else:
            formatter = None
        if bins == None:
            if self.laod:
                bins = arange(-5., 1., 0.01 )
            else:
                bins = arange(0., 0.6, 0.01 )
        x_bins = bins
        y_bins = bins
        if len(targets.shape) == 1:
            x_values = targets
            y_values = results.squeeze()
        else:
            x_values = targets[:,0]            
            y_values = results[:,0]
        _plotKDE(x_values,y_values,x_bins,y_bins,y_label='NNR',
                 formatter=formatter,x_label=x_label)        
        title("Log("+self.Target[0][1:]+"+{}) - ".format(self.logoffset)+self.ident)
        if figfile != None:
            savefig(figfile)
            
    def plotScat(self,iTarget=0,bins=None,I=None,figfile=None):
        """
        Plot Target vs Model as a scatter plot
        """
        if I is None: I = self.iTest # Testing data by default
        results = self.eval(I)[:,iTarget]
        targets = self.getTargets(I)
        if self.scale:
            targets = self.scaler.inverse_transform(targets)
        if self.nTarget > 1:
            targets = targets[:,iTarget]
        if not self.laod:
            results = np.log(results + self.logoffset)
            targets = np.log(targets + self.logoffset)
        original = log(self.__dict__['m'+self.Target[iTarget][1:]][I] + self.logoffset)
        if bins == None:
            bins = arange(-5., 1., 0.1 )

        figure()
        plot(targets,original,'bo',label='Original')
        plot(targets,results,'ro',label='Corrected')
        legend(loc='upper left')
        plot(bins,bins,'k')
        grid()
        xlabel('AERONET')
        ylabel('MODIS')
        title("Log("+self.Target[iTarget][1:]+"+{}) - ".format(self.logoffset)+self.ident)
        if figfile != None:
            savefig(figfile)
#---------------------------------------------------------------------------------
def _cat2 (X, Y):
    """
    Given 2 arrays of same shape, returns array of shape (2,N),
    where N = X.size = Y.size
    """
    xy = concatenate((X.ravel(),Y.ravel())) # shape is (N+N)
    return reshape(xy,(2,X.size))         # shape is (2,N)
    
def _plotKDE(x_values,y_values,x_bins=None,y_bins=None,
             x_label='AERONET', y_label='MODIS',formatter=None):
        """
        Plot Target vs Model using a 2D Kernel Density Estimate.
        """

        if x_bins is None: x_bins = arange(-5., 1., 0.1 )
        if y_bins is None: y_bins = x_bins

        Nx = len(x_bins)
        Ny = len(y_bins)

        print("Evaluating 2D kernel on grid with (Nx,Ny)=(%d,%d) ..."%(Nx,Ny))
        kernel = stats.kde.gaussian_kde(_cat2(x_values,y_values))
        X, Y = meshgrid(x_bins,y_bins)   # each has shape (Ny,Nx)
        Z = kernel(_cat2(X,Y))           # shape is (Ny*Nx)
        Z = reshape(Z,X.shape)

        fig = figure()
        # ax = fig.add_axes([0.1,0.1,0.75,0.75])
        ax = fig.add_axes([0.1,0.1,0.75,0.75])
        if formatter != None:
            ax.xaxis.set_major_formatter(formatter)
            ax.yaxis.set_major_formatter(formatter)
        imshow(Z, cmap=cm.gist_earth_r, origin='lower', 
               extent=(x_bins[0],x_bins[-1],y_bins[0],y_bins[-1]) )
        plot([x_bins[0],x_bins[-1]],[y_bins[0],y_bins[-1]],'k')
        xlabel(x_label)
        ylabel(y_label)
        grid()

        return fig
