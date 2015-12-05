import time
import numpy as np
import AuxiliaryClass as AUX
from scipy.sparse import spdiags as spdiags
import scipy.sparse as sparse

np.set_printoptions(threshold = 3000, linewidth=2000, suppress=True)

def Multi_Country(S,I,sigma):

    #NOTE:To run the model, simply run the Multi_Country function with your chosen levels
    #of the number of cohorts (S), the number of countries (I) and slope parameter (sigma)

    #THIS SETS ALL OF THE USER PARAMETERS

    #Country Rosters
    I_dict = {"usa":0,"eu":1,"japan":2,"china":3,"india":4,"russia":5,"korea":6}
    I_touse = ["eu","russia","usa","japan","korea","china","india"] 

    #Parameters Zone
    g_A = 0.015 #Technical growth rate
    beta_ann=.95 #Annual discount rate
    delta_ann=.08 #Annual depreciation rate
    alpha = .3 #Capital Share of production
    chi = 1.5 #Preference for lesiure
    rho = 1.3 #Other New Parameter

    #Convergence Tolerances
    tpi_tol = 1e-8 #Convergence Tolerance
    demog_ss_tol = 1e-8 #Used in getting ss for population share
    xi = .9999 #Parameter used to take the convex conjugate of paths
    MaxIters = 10000 #Maximum number of iterations on TPI.

    #Program Levers
    CalcTPI = True #Activates the calculation of Time Path Iteration

    PrintAges = False #Prints the different key ages in the demographics
    PrintLoc = False #Displays the current locations of the program inside key TPI functions
    PrintEulErrors = True #Prints the euler errors in each attempt of calculating the steady state
    PrintSS = True #Prints the result of the Steady State functions
    Print_cabqTimepaths = False #Prints the consumption, assets, and bequests timepath as it gets filled in for each iteration of TPI

    CheckerMode = False #Reduces the number of prints when checking for robustness, use in conjunction with RobustChecker.py

    DemogGraphs = False #Activates graphing graphs with demographic data and population shares
    TPIGraphs = False #Activates showing the final graphs

    IterGraphs = True
    IterationsToShow = set([]) #List the iteration numbers you wish to observe, IterGraphs must be ON

    UseStaggeredAges = True #Activates using staggered ages
    UseDiffDemog = True #Turns on different demographics for each country
    UseSSDemog = True #Activates using only steady state demographics for TPI calculation
    ShowSSGraphs = False
    UseDiffProductivities = False #Activates having e vary across cohorts
    UseTape = True #Activates setting any value of kd<0 to 0.001 in TPI calculation

    CalcTPI = True

    SAVE = False #Saves the graphs
    SHOW = True #Shows the graphs
    ADJUSTKOREAIMMIGRATION = True #Adjusts demograhpics to correct for oddities in Korea's data.

    #Adjusts the country list if we are using less than 7 Countries
    if len(I_touse) < I:
        print "WARNING: We are changing I from", I, "to", len(I_touse), "to fit the length of I_touse. So the countries we are using now are", I_touse
        I = len(I_touse)
        time.sleep(2)
    elif len(I_touse) > I:
        print "WARNING: We are changing I_touse from", I_touse, "to", I_touse[:I], "so there are", I, "regions"
        I_touse = I_touse[:I]
        time.sleep(2)


    ##INPUTS INTO THE CLASS###

    Country_Roster = (I_dict, I_touse)

    HH_params = (S,I,beta_ann,sigma)

    Firm_Params = (alpha, delta_ann, chi, rho, g_A)

    Tolerances = (tpi_tol, demog_ss_tol)

    Levers = (CalcTPI, PrintAges,PrintLoc,PrintEulErrors,PrintSS,ShowSSGraphs,Print_cabqTimepaths,CheckerMode,DemogGraphs,IterGraphs,TPIGraphs,\
            UseStaggeredAges,UseDiffDemog,UseSSDemog,UseDiffProductivities,UseTape,SAVE,SHOW,ADJUSTKOREAIMMIGRATION)

    Sets = (IterationsToShow)

    TPI_Params = (xi,MaxIters)



    ##WHERE THE MAGIC HAPPENS ##

    Model = AUX.OLG(Country_Roster,HH_params,Firm_Params,Levers, Sets, Tolerances, TPI_Params)

    #Demographics
    Model.Import_Data()
    Model.Demographics()

    #Steady State

    #STEADY STATE INITIAL GUESSES

    r_ss_guess = .2
    bq_ss_guess = np.ones(I)*.2
    Model.SteadyState(r_ss_guess, bq_ss_guess)


    #Timepath Iteration
    
    r_init = Model.r_ss*.98
    bq_init = Model.bq_ss*.98
    a_init = Model.avec_ss*.98
    Model.set_initial_values(r_init, bq_init, a_init)
    if CalcTPI: Model.Timepath()
    if TPIGraphs: Model.plotTimepaths()

    pass


#Input parameters for S, I and sigma here then execute this file to
#run the model.
Multi_Country(20,3,4)