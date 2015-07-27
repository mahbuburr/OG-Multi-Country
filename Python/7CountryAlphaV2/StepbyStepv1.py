from __future__ import division
import numpy as np
import scipy.optimize as opt

"""
#Size of asset matrix
#OOPS. Forgot correct size of e matrix
#How do we get the initial consumption values for generations that haven't been born yet?
"""

#Describe what they are
S = 4
Countries = 2
T = 8
beta = .9
sigma = 3
delta = .01
alpha = .5
e = np.ones((Countries, S, T+S))
A = np.ones((Countries, T))

#STEADY STATE FUNCTIONS

def getOtherVariables(assets, kf):
    	"""
    	Description:
        	Based on the assets and capital held by foreigners, we calculate the other variables.
    	Inputs:
        	-assets: Matrix of assets
        	-kf: Domestic capital held by foreigners
    	Output:
        	-k: Capital
        	-n: Sum of labor productivities
        	-y: Output
        	-r: Rental Rate
        	-w: Wage
        	-c_vec: Vector of consumptions

    	"""
	
	k = np.sum(assets[:,1:-1], axis=1) - kf
	n = np.sum(e[:,:,0], axis=1)
	y = (k**alpha) * ((A[:,0]*n)**(1-alpha))
	r = alpha * y / k
	w = (1-alpha) * y / n

	c_vec = np.einsum("i, is -> is", w, e[:,:,0]) + np.einsum("i, is -> is",(1 + r - delta) , assets[:,:-1]) - assets[:,1:]

	return k, n, y, r, w, c_vec

def SteadyStateSolution(guess):
    	"""
    Description: 
    	This is the function that will be optimized by fsolve.
    Inputs:
    	-guess:vector that pieced together from assets and kf.
    Output:
        -all_Euler:Similar to guess, it's a vector that's has both assets and kf.
    	
    	"""
	#Takes a 1D guess of length Countries*S and reshapes it to match what the original input into the fsolve looked like since fsolve flattens numpy arrays
	guess = np.reshape(guess[:,np.newaxis], (Countries, S))

	#Sets kf as the last element of the guess vector for each country and assets as everything else
	assets = guess[:,:-1]
	kf = guess[:,-1]

	#You have 0 assets when you're born, and 0 when you die
	assets = np.column_stack((np.zeros(Countries), assets, np.zeros(Countries)))

	#Self explanitory
	k, n, y, r, w, c_vec = getOtherVariables(assets, kf)

	#Gets Euler equations
	Euler_c = c_vec[:,:-1] ** (-sigma) - beta * c_vec[:,1:] ** (-sigma) * (1 + r[0] - delta)
	Euler_r = r[1:] - r[0]
	Euler_kf = np.sum(kf)

	#Makes a new 1D vector of length Countries*S that contains all the Euler equations
	all_Euler = np.append(np.append(np.ravel(Euler_c), np.ravel(Euler_r)), Euler_kf)

	return all_Euler

def getSteadyState(assets_init, kf_init):
	"""
	Description:
        This takes the initial guess for assets and kf. Since the function
	    returns a matrix, this unpacks the individual parts.
	Inputs:
	    -assets_init:Intial guess for asset path
	    -kf_init:Initial guess on foreigner held capital  
	Outputs:
	    -assets_ss:Calculated assets steady state
	    -kf_ss:Calculated foreign capital
	"""

	guess = np.column_stack((assets_init, kf_init))

	ss = opt.fsolve(SteadyStateSolution, guess)

	print "\nSteady State Found!\n"
	ss = np.array(np.split(ss, Countries))
	assets_ss = ss[:,:-1]
	kf_ss = ss[:,-1]

        return assets_ss, kf_ss

#TIMEPATH FUNCTIONS

def get_householdchoices_path(c_1, wpath_chunk, rpath_chunk, e_chunk, starting_assets, current_s):
	"""
	Description:
		This solves for equations 1.15 and 1.16 in the StepbyStep pdf for a certain generation
	Inputs:
	    -c_1: Initial consumption (not necessarily for the year they were born)
	    -wpath_chunk: Wages of an agents lifetime, a section of the timepath
	    -rpath_chunk: Rental rate of an agents lifetime, a section of the timepath
	    -e_chunk: Worker productivities of an agents lifetime, a section of the global matrix
	    -starting_assets: Initial assets of the agent. Will be 0s if we are beginning in the year the agent was born
	    -current_s: Current age of the agent
	Outputs:
	    -c_path: Path of consumption until the agent dies
	    -asset_path: Path of assets until the agent dies
	"""

	c_path = np.zeros((Countries, S))
	asset_path = np.zeros((Countries, S+1))

	c_path[:,0] = c_1
	asset_path[:,0] = starting_assets

	for s in range(1,S):
		c_path[:,s] = (beta * (1 + rpath_chunk[:,s] - delta))**(1/sigma) * c_path[:,s-1]
		asset_path[:,s] = wpath_chunk[:,s]*e[:,0,s-1] + (1 + rpath_chunk[:,s-1] - delta)*asset_path[:,s-1] - c_path[:,s-1]

	asset_path[:,s+1] = wpath_chunk[:,s]*e_chunk[:,s] + (1 + rpath_chunk[:,s] - delta)*asset_path[:,s] - c_path[:,s]

	#Document this 
	return c_path[:,0:S-current_s], asset_path[:,0:S+1-current_s]

def find_optimal_starting_consumptions(c_1, wpath_chunk, rpath_chunk, epath_chunk, starting_assets, current_s):
        """
        Description:
            Takes the assets path from the get_householdchoices_path function and creates  
        Inputs:
            -c_1: Initial consumption (not necessarily for the year they were born)
            -wpath_chunk: Wages of an agents lifetime, a part of the timepath
            -rpath_chunk: Rental rate of an agents lifetime, another part of the timeparth.
            -epath_chunk: Worker productivities of an agents lifetime, another part.
            -starting_assets: Initial assets of the agent. It's 0 at the beginning of life.
            -current_s: Current age of the agent

        Outputs:
            -Euler:A flattened version of the assets_path matrix

        """

	c_path, assets_path = get_householdchoices_path(c_1, wpath_chunk, rpath_chunk, epath_chunk, starting_assets, current_s)

	Euler = np.ravel(assets_path[:,-1])

	return Euler

def get_prices(assets_tpath, kf_tpath):
    	"""
    Description:
        Based on the given paths, the paths for wages and rental rates are figured
        out based on equations 1.4-1.5

    Inputs:
        -assets_tpath: Asset timepath
        -kf_tpath: Foreign held capital timepath.

    Outputs:
        -wpath: Wage path
        -rpath: Rental rate path

    	"""

	#Gets non-price variables needed to caluclate prices
	kpath = np.sum(assets_tpath[:,1:-1,:-1], axis=1) - kf_tpath[:,:-1]
	n = np.sum(e, axis=1)
	ypath = (kpath**alpha) * ((A*n)**(1-alpha))

	#Gets prices
	rpath = alpha * ypath / kpath
	wpath = (1-alpha) * ypath / n

	#Stacks extra year of steady state for later code that tries to use outside index
	rpath = np.column_stack((rpath, rpath[:,-1]))
	wpath = np.column_stack((wpath, wpath[:,-1]))

	#Returns only the first country's interest rate, since they should be the same in theory
	return wpath, rpath#[0,:]

def get_wpath1_rpath1(w_path0, r_path0):#UNDER CONSTRUCTION
        """
        Description:
            Takes initial paths of wages and rental rates

        Inputs:
            -w_path0
            -r_path0
        Outputs:
            This will output w_path1 and r_path1, matrices to compare to w_path0 and r_path0 to see if we have a correct timepath

        """
    #Initializes timepath variables
	c_timepath = np.zeros((Countries,S,T+1))
	test = np.zeros((Countries,S,T+1))
	assets_timepath = np.zeros((Countries,S+1, T+1))

	#Makes an initial guess for fsolve. Will be used in each generation
	c_guess = np.ones(Countries)*.2

	#Fills the upper triangle
	for s in range(S):
		starting_assets = np.array([.1*s, .1*s])#This is zero if s is zero

		#We are only doing this for all generations alive in time t=0
		t = 0
		#We are iteration through each generation in time t=0
		current_s = s

		#Gets optimal initial consumption beginning in the current age of the agent using chunks of w and r that span the lifetime of the given generation
		
		#NOTE: SUBTRACT CURRENT_S FROM THE LAST PART OF THE CHUNK TO NOT GIVE MORE THAN WE NEED?
		opt_consump_1 = opt.fsolve(find_optimal_starting_consumptions, c_guess, args = (w_path0[:,t:t+S], r_path0[:,t:t+S], e[:,0,t:t+S], starting_assets, current_s))
		opt_consump_test = opt.fsolve(find_optimal_starting_consumptions, c_guess, args = (w_path0[:,t:t+S+S-1-current_s], r_path0[:,t:t+S+S-1-current_s], e[:,0,t:t+S+S-1-current_s], starting_assets, current_s))

		print np.argwhere(opt_consump_1 != opt_consump_test), w_path0[:,t:t+S].shape, w_path0[:,t:t+S+S-1-current_s].shape
		#Gets optimal timepaths beginning initial consumption and starting assets
		cpath_indiv, assetpath_indiv = get_householdchoices_path(opt_consump_1, w_path0[:,t:t+S], r_path0[:,t:t+S], e[:,0,t:t+S], starting_assets, current_s)

		#Just sets assets after death to zero. It will be super close to zero thanks to the euler equation in fsolve, but setting it to zero makes it easier to look at and check for errors
		assetpath_indiv[:,-1] = 0

		for i in range(Countries):
			np.fill_diagonal(c_timepath[i,s:s+S,:], cpath_indiv[i,:])
			np.fill_diagonal(assets_timepath[i,s:s+S,:], assetpath_indiv[i,:])

	#Fills everything except for the upper triangle
	for t in range(1,T):
		current_s = 0
		starting_assets = np.zeros((Countries))

		optimalconsumption = opt.fsolve(find_optimal_starting_consumptions, c_guess, args = (w_path0[:,t:t+S], r_path0[:,t:t+S], e[:,0,t:t+S], starting_assets, current_s))

		cpath_indiv, assetpath_indiv = get_householdchoices_path(optimalconsumption, w_path0[:,t:t+S], r_path0[:,t:t+S], e[:,0,t:t+S], starting_assets, current_s)

		assetpath_indiv[:,-1] = 0

		for i in range(Countries):
			np.fill_diagonal(c_timepath[i,:,t:], cpath_indiv[i,:])
			np.fill_diagonal(assets_timepath[i,:,t:], assetpath_indiv[i,:])

	w_path1, r_path1 = get_prices()
	
#MAIN CODE

#Initalizes initial guesses
assets_guess = np.ones((Countries, S-1))*.15
kf_guess = np.zeros((Countries))
w_initguess = np.zeros((Countries, T+1+S))
r_initguess = np.zeros((Countries, T+1+S))

#Gets the steady state variables
assets_ss, kf_ss = getSteadyState(assets_guess, kf_guess)
k_ss, n_ss, y_ss, r_ss, w_ss, c_vec_ss = getOtherVariables(np.column_stack((np.zeros(Countries), assets_ss, np.zeros(Countries))), kf_ss)

#Sets initial assets and kf
assets_init = assets_ss/2
kf_init = kf_ss/2

#Gets initial k, n, y, r, w, and c
k_init, n_init, y_init, r_init, w_init, c_vec_init = getOtherVariables(np.column_stack((np.zeros(Countries), assets_init, np.zeros(Countries))), kf_init)

#Gets initial guess for w and r paths
for c in range(Countries):
	w_initguess[c, :T+1] = np.linspace(w_init[c], w_ss[c], T+1)
	r_initguess[c, :T+1] = np.linspace(r_init[c], r_ss[c], T+1)
	w_initguess[c,T+1:] = w_initguess[c,T]
	r_initguess[c,T+1:] = r_initguess[c,T]

#Gets new paths for wages and rental rates to see how close it is to the original code
get_wpath1_rpath1(w_initguess, r_initguess)



 