#!/usr/bin/env python
import numpy as np
import os
import argparse
import pylab as pl
import subprocess as sp
import astropy.io.fits as pyfits
import pandas as pd
import scipy.special as ss
import om10_lensing_equations as ole
import sqlite3 as sql

#data_dir = os.path.join(os.environ['SIMS_GCRCATSIMINTERFACE_DIR'], 'data')
data_dir = 'data/'
twinkles_data_dir = data_dir #os.path.join(os.environ['TWINKLES_DIR'], 'data')
outdefault = 'outputs' #os.path.join(data_dir,'outputs')

parser = argparse.ArgumentParser(description='The location of the desired output directory')
parser.add_argument("--outdir", dest='outdir1', type=str, default = outdefault,
                    help='Output location for FITS stamps')
args = parser.parse_args()
outdir = args.outdir1

def load_in_data_agn():

    """
    Reads in catalogs of host galaxy bulge and disk as well as om10 lenses

    Returns:
    -----------
    lens_list: data array for lenses.  Includes t0, x, y, sigma, gamma, e, theta_e     
    ahb_purged: Data array for galaxy bulges.  Includes prefix, uniqueId, raPhoSim, decPhoSim, phosimMagNorm   
    ahd_purged: Data array for galaxy disks.  Includes prefix, uniqueId, raPhoSim, decPhoSim, phosimMagNorm

    """
    #agn_host_bulge = pd.read_csv(os.path.join(twinkles_data_dir,
    #                             'cosmoDC2_v1.1.4_bulge_agn_host.csv'))
    #agn_host_disk = pd.read_csv(os.path.join(twinkles_data_dir,
     #                           'cosmoDC2_v1.1.4_disk_agn_host.csv'))

    conn = sql.connect(os.path.join(data_dir,'host_truth.db'))
    agn_host = pd.read_sql_query("select * from agn_hosts;", conn)

    #idx = agn_host['image_number'] == 0
    ahb_purged = agn_host#[:][idx]
   
    lens_list = pyfits.open(os.path.join(twinkles_data_dir, 'cosmoDC2_v1.1.4_matched_AGN.fits'))

    return lens_list, ahb_purged 


def create_cats_agns(index, hdu_list, ahb_list):
    """
    Takes input catalogs and isolates lensing parameters as well as ra and dec of lens     

    Parameters:
    -----------
    index: int
        Index for pandas data frame
    hdu_list:
        row of data frame that contains lens parameters
    ahb_list:
        row of data frame that contains lens galaxy parameters for the galactic bulge

    Returns:
    -----------
    lens_cat: Data array that includes lens parameters
    srcsP_bulge: Data array that includes parameters for galactic bulge
    srcsP_disk: Data array that includes parameters for galactic disk
    """
    twinkles_ID = ahb['index'][index]
    
    UID_lens = ahb['lens_cat_sys_id'][index]
    Ra_lens = ahb['ra_lens'][index]
    Dec_lens = ahb['dec_lens'][index]
    idx = hdu_list[1].data['twinklesid'] == twinkles_ID

    #nrows1 = hdu_list[1].data.shape[0]

    lid = hdu_list[1].data['LENSID'][idx][0]
    xl1 = 0.0
    xl2 = 0.0
    vd = hdu_list[1].data['VELDISP'][idx][0]
    zd = hdu_list[1].data['ZLENS'][idx][0]
    ql  = 1.0 - hdu_list[1].data['ELLIP'][idx][0]
    phi= hdu_list[1].data['PHIE'][idx][0]

    ys1 = hdu_list[1].data['XSRC'][idx][0]
    ys2 = hdu_list[1].data['YSRC'][idx][0]

    ext_shr = hdu_list[1].data['GAMMA'][idx][0]
    ext_phi = hdu_list[1].data['PHIG'][idx][0]

    ximg = hdu_list[1].data['XIMG'][idx][0]
    yimg = hdu_list[1].data['YIMG'][idx][0]

    #----------------------------------------------------------------------------
    lens_cat = {'xl1'        : xl1,
                'xl2'        : xl2,
                'ql'         : ql,
                'vd'         : vd,
                'phl'        : phi,
                'gamma'      : ext_shr,
                'phg'        : ext_phi,
                'zl'         : zd,
                'ximg'       : ximg,
                'yimg'       : yimg,
                'twinklesid' : twinkles_ID,
                'lensid'     : lid,
                'index'      : index,
                'UID_lens'   : UID_lens,
                'Ra_lens'    : Ra_lens,
                'Dec_lens'   : Dec_lens}
    
    #----------------------------------------------------------------------------

    mag_src_b_u = ahb_list['magnorm_bulge_u'][index]
    mag_src_b_g = ahb_list['magnorm_bulge_g'][index]
    mag_src_b_r = ahb_list['magnorm_bulge_r'][index]
    mag_src_b_i = ahb_list['magnorm_bulge_i'][index]
    mag_src_b_z = ahb_list['magnorm_bulge_z'][index]
    mag_src_b_y = ahb_list['magnorm_bulge_y'][index]

    qs_b = ahb_list['minor_axis_bulge'][index]/ahb_list['major_axis_bulge'][index]
    Reff_src_b = np.sqrt(ahb_list['minor_axis_bulge'][index]*ahb_list['major_axis_bulge'][index])
    phs_b = ahb_list['position_angle'][index]
    ns_b = ahb_list['sindex_bulge'][index]
    zs_b = ahb_list['redshift'][index]
    sed_src_b = ahb_list['sed_bulge_host'][index]
    
    srcsP_bulge = {'ys1'          : ys1,
                   'ys2'          : ys2,
                   'mag_src_u'      : mag_src_b_u,
                   'mag_src_g'      : mag_src_b_g,
                   'mag_src_r'      : mag_src_b_r,
                   'mag_src_i'      : mag_src_b_i,
                   'mag_src_z'      : mag_src_b_z,
                   'mag_src_y'      : mag_src_b_y,
                   'Reff_src'     : Reff_src_b,
                   'qs'           : qs_b,
                   'phs'          : phs_b,
                   'ns'           : ns_b,
                   'zs'           : zs_b,
                   'sed_src'      : sed_src_b,                         
                   'components'   : 'bulge'}
    
    #----------------------------------------------------------------------------
    mag_src_d_u = ahb_list['magnorm_disk_u'][index]
    mag_src_d_g = ahb_list['magnorm_disk_g'][index]
    mag_src_d_r = ahb_list['magnorm_disk_r'][index]
    mag_src_d_i = ahb_list['magnorm_disk_i'][index]
    mag_src_d_z = ahb_list['magnorm_disk_z'][index]
    mag_src_d_y = ahb_list['magnorm_disk_y'][index]

    qs_d = ahb_list['minor_axis_disk'][index]/ahb_list['major_axis_disk'][index]
    Reff_src_d = np.sqrt(ahb_list['minor_axis_disk'][index]*ahb_list['major_axis_disk'][index])
    phs_d = ahb_list['position_angle'][index]
    ns_d = ahb_list['sindex_disk'][index]
    zs_d = ahb_list['redshift'][index]
    sed_src_d = ahb_list['sed_disk_host'][index]

    srcsP_disk = {'ys1'          : ys1,
                  'ys2'          : ys2,
                  'mag_src_u'      : mag_src_d_u,
                  'mag_src_g'      : mag_src_d_g,
                  'mag_src_r'      : mag_src_d_r,
                  'mag_src_i'      : mag_src_d_i,
                  'mag_src_z'      : mag_src_d_z,
                  'mag_src_y'      : mag_src_d_y,
                  'Reff_src'     : Reff_src_d,
                  'qs'           : qs_d,
                  'phs'          : phs_d,
                  'ns'           : ns_d,
                  'zs'           : zs_d,
                  'sed_src'      : sed_src_d,
                  'components'   : 'disk'}
    
    #----------------------------------------------------------------------------

    return lens_cat, srcsP_bulge, srcsP_disk


def lensed_sersic_2d(xi1, xi2, yi1, yi2, source_cat, lens_cat):
    """Defines a magnitude of lensed host galaxy using 2d Sersic profile 
    Parameters:
    -----------
    xi1: x-position of lens (pixel coordinates)
    xi2: y-position of lens (pixel coordinates)
    yi1: x-position of source bulge or disk (pixel coordinates)
    yi2: y-position of source bulge or disk (pixel coordinates)
    source_cat: source parameters
    lens_cat: lens parameters, from create_cats_sne()

    Returns:
    -----------
    mag_lensed: Lensed magnitude for host galaxy
    g_limage: Lensed image (array of electron counts)
    """
    #----------------------------------------------------------------------
    ysc1     = source_cat['ys1']        # x position of the source, arcseconds
    ysc2     = source_cat['ys2']        # y position of the source, arcseconds
    mag_tot_u  = source_cat['mag_src_u']    # total magnitude of the source
    mag_tot_g  = source_cat['mag_src_g']    # total magnitude of the source
    mag_tot_r  = source_cat['mag_src_r']    # total magnitude of the source
    mag_tot_i  = source_cat['mag_src_i']    # total magnitude of the source
    mag_tot_z  = source_cat['mag_src_z']    # total magnitude of the source
    mag_tot_y  = source_cat['mag_src_y']    # total magnitude of the source
    Reff_arc = source_cat['Reff_src']   # Effective Radius of the source, arcseconds
    qs       = source_cat['qs']         # axis ratio of the source, b/a
    phs      = source_cat['phs']        # orientation of the source, degree
    ns       = source_cat['ns']         # index of the source

    #----------------------------------------------------------------------

    g_limage = ole.sersic_2d(yi1,yi2,ysc1,ysc2,Reff_arc,qs,phs,ns)
    g_source = ole.sersic_2d(xi1,xi2,ysc1,ysc2,Reff_arc,qs,phs,ns)

    mag_lensed_u = mag_tot_u - 2.5*np.log10(np.sum(g_limage)/np.sum(g_source))
    mag_lensed_g = mag_tot_g - 2.5*np.log10(np.sum(g_limage)/np.sum(g_source))
    mag_lensed_r = mag_tot_r - 2.5*np.log10(np.sum(g_limage)/np.sum(g_source))
    mag_lensed_i = mag_tot_i - 2.5*np.log10(np.sum(g_limage)/np.sum(g_source))
    mag_lensed_z = mag_tot_z - 2.5*np.log10(np.sum(g_limage)/np.sum(g_source))
    mag_lensed_y = mag_tot_y - 2.5*np.log10(np.sum(g_limage)/np.sum(g_source))

    return mag_lensed_u, mag_lensed_g, mag_lensed_r, mag_lensed_i, mag_lensed_z, mag_lensed_y, g_limage


def generate_lensed_host(xi1, xi2, lens_P, srcP_b, srcP_d):
    """Does ray tracing of light from host galaxies using a non-singular isothermal ellipsoid profile.  
    Ultimately writes out a FITS image of the result of the ray tracing.      
    Parameters:
    -----------
    xi1: x-position of lens (pixel coordinates)
    xi2: y-position of lens (pixel coordinates)
    lens_P: Data array of lens parameters (takes output from create_cats_sne)  
    srcP_b: Data array of source bulge parameters (takes output from create_cats_sne) 
    srcP_d: Data array of source disk parameters (takes output from create_cats_sne) 

    Returns:
    -----------

    """
    dsx  = 0.01
    xlc1 = lens_P['xl1']                # x position of the lens, arcseconds
    xlc2 = lens_P['xl2']                # y position of the lens, arcseconds
    rlc  = 0.0                          # core size of Non-singular Isothermal Ellipsoid
    vd   = lens_P['vd']                 # velocity dispersion of the lens
    zl   = lens_P['zl']                 # redshift of the lens
    zs   = srcP_b['zs']                 # redshift of the source
    rle  = ole.re_sv(vd, zl, zs)        # Einstein radius of lens, arcseconds.
    ql   = lens_P['ql']                 # axis ratio b/a
    le   = ole.e2le(1.0 - ql)           # scale factor due to projection of ellipsoid
    phl  = lens_P['phl']                # position angle of the lens, degree
    eshr = lens_P['gamma']              # external shear
    eang = lens_P['phg']                # position angle of external shear
    ekpa = 0.0                          # external convergence

    #----------------------------------------------------------------------
    ai1, ai2 = ole.alphas_sie(xlc1, xlc2, phl, ql, rle, le,
                              eshr, eang, ekpa, xi1, xi2)

    yi1 = xi1 - ai1
    yi2 = xi2 - ai2
    #----------------------------------------------------------------------------
    
    lensed_mag_b_u, lensed_mag_b_g, lensed_mag_b_r, lensed_mag_b_i, lensed_mag_b_z, lensed_mag_b_y, lensed_image_b = lensed_sersic_2d(xi1,xi2,yi1,yi2,srcP_b,lens_P)

    os.makedirs(os.path.join(outdir,'agn_lensed_bulges'), exist_ok=True)

    fits_limg_b = os.path.join(outdir,'agn_lensed_bulges/') + str(lens_P['UID_lens']) + "_" + str(rle)+ "_" + str(lensed_mag_b_u)+"_"+str(lensed_mag_b_g)+"_"+str(lensed_mag_b_r)+"_"+str(lensed_mag_b_i)+"_"+str(lensed_mag_b_z)+"_"+str(lensed_mag_b_y)+ "_bulge.fits" 
 
    pyfits.writeto(fits_limg_b, lensed_image_b.astype("float32"), overwrite=True)

    #----------------------------------------------------------------------------

    lensed_mag_d_u, lensed_mag_d_g, lensed_mag_d_r, lensed_mag_d_i, lensed_mag_d_z, lensed_mag_d_y, lensed_image_d = lensed_sersic_2d(xi1,xi2,yi1,yi2,srcP_d,lens_P)

    os.makedirs(os.path.join(outdir,'agn_lensed_disks'), exist_ok=True)

    fits_limg_d = os.path.join(outdir,'agn_lensed_disks/') + str(lens_P['UID_lens']) + "_" +str(rle)+ "_" + str(lensed_mag_d_u)+"_" +str(lensed_mag_d_g)+"_"+str(lensed_mag_d_r)+"_"+str(lensed_mag_d_i)+"_"+str(lensed_mag_d_z)+"_"+str(lensed_mag_d_y)+ "_disk.fits" 
 
    pyfits.writeto(fits_limg_d, lensed_image_d.astype("float32"), overwrite=True)

    return 0


if __name__ == '__main__':

    dsx = 0.01  # pixel size per side, arcseconds
    nnn = 1000  # number of pixels per side
    xi1, xi2 = ole.make_r_coor(nnn, dsx)

    hdulist, ahb = load_in_data_agn()

    #hdulist is the list of lens parameters
    #ahb is the list of galaxy bulge and disk parameters

    message_row = 0
    message_freq = 50
    for i, row in ahb.iterrows():
        if i >= message_row:
            print ("working on system ", i , "of", max(ahb.index))
            message_row += message_freq
        lensP, srcPb, srcPd = create_cats_agns(i, hdulist, ahb)
        load_in_data_agn()
        generate_lensed_host(xi1, xi2, lensP, srcPb, srcPd)    