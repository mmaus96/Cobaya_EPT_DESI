import numpy as np

from classy import Class
from linear_theory import f_of_a
# from velocileptors.LPT.lpt_rsd_fftw import LPT_RSD
from velocileptors.EPT.ept_fullresum_fftw import REPT
from pnw_dst import pnw_dst

# k vector to use:
# kvec = np.concatenate( ([0.0005,],\
#                         np.logspace(np.log10(0.0015),np.log10(0.025),10, endpoint=True),\
#                         np.arange(0.03,0.51,0.01)) )

kmin = 5e-3
kmax = 0.5
nk = 100

kvec = np.logspace(np.log10(kmin), np.log10(kmax), nk)


def compute_pell_tables(pars, z=0.8, fid_dists= (None,None), kmin = 5e-3, kmax = 0.5, nk = 100,ap_off=False ):
    
    omega_b,omega_cdm, h, sigma8 = pars
    Hzfid, chizfid = fid_dists
    speed_of_light = 2.99792458e5

    # omega_b = 0.02242

    As =  2.0830e-9
    ns = 0.9649

    nnu = 1
    nur = 2.0328
    # mnu = 0.06
    omega_nu = 0.0006442 #0.0106 * mnu
    # mnu = omega_nu / 0.0106
        
    # omega_c = (OmegaM - omega_b/h**2 - omega_nu/h**2) * h**2
    OmegaM = (omega_cdm + omega_b + omega_nu) / h**2

    pkparams = {
        'output': 'mPk',
        'P_k_max_h/Mpc': 20.,
        'z_pk': '0.0,10',
        'A_s': As,
        'n_s': ns,
        'h': h,
        'N_ur': nur,
        'N_ncdm': nnu,
        'omega_ncdm': omega_nu,
        # 'm_ncdm': mnu,
        'tau_reio': 0.0568,
        'omega_b': omega_b,
        'omega_cdm': omega_cdm}

    pkclass = Class()
    pkclass.set(pkparams)
    pkclass.compute()

    # Caluclate AP parameters
    Hz = pkclass.Hubble(z) * speed_of_light / h # this H(z) in units km/s/(Mpc/h) = 100 * E(z)
    chiz = pkclass.angular_distance(z) * (1.+z) * h # this is the comoving radius in units of Mpc/h 
    apar, aperp = Hzfid / Hz, chiz / chizfid
    
    if ap_off:
        apar, aperp = 1.0, 1.0
    
    # Calculate growth rate
    fnu = pkclass.Omega_nu / pkclass.Omega_m()
    f   = f_of_a(1/(1.+z), OmegaM=OmegaM) * (1 - 0.6 * fnu)

    # Calculate and renormalize power spectrum
    ki = np.logspace(-3.0,1.0,200)
    pi = np.array( [pkclass.pk_cb(k*h, z ) * h**3 for k in ki] )
    pi = (sigma8/pkclass.sigma8())**2 * pi
    
    _,pnw = pnw_dst(ki,pi)
    pw = pi-pnw
    
    # Now do the RSD
    # modPT = LPT_RSD(ki, pi, kIR=0.2,\
    #             cutoff=10, extrap_min = -4, extrap_max = 3, N = 2000, threads=1, jn=5)
    # modPT.make_pltable(f, kv=kvec, apar=apar, aperp=aperp, ngauss=3)
    modPT = REPT(ki, pi, pnw=pnw, kmin = 5e-3, kmax = 0.5, nk = 100,\
           beyond_gauss=True, one_loop= True,\
           N = 2000, extrap_min=-6, extrap_max=3, cutoff = 100, threads=1)
    
    modPT.compute_redshift_space_power_multipoles_tables(f, ngauss=4, apar=apar, aperp=aperp)
    
    return modPT.kv, modPT.p0ktable, modPT.p2ktable, modPT.p4ktable
    