'''
--------------------------------------------------------------------
This is Bobae's Python script for MACS 40200 PS4.
--------------------------------------------------------------------
'''
# Import packages and load the data
import numpy as np
import numpy.linalg as lin
from pandas import Series, DataFrame
import scipy.stats as sts
import scipy.special as spc
import scipy.integrate as intgr
import scipy.optimize as opt
import matplotlib.pyplot as plt
import seaborn
import os

# set the directory for saving images
cur_path = os.path.split(os.path.abspath(__file__))[0]
output_fldr = 'images'
output_dir = os.path.join(cur_path, output_fldr)
if not os.access(output_dir, os.F_OK):
    os.makedirs(output_dir)

# read the data
incmoms = DataFrame(np.loadtxt('usincmoms.txt'))

# setup for plotting
incvals = incmoms[1]/1000

incbins = list(incmoms[1]/1000 - 2.5)
incbins[40] = 200.0
incbins[41] = 250.0
incbins.append(350.0)

incweights = list(incmoms[0])
incweights[40] = incweights[40]/10
incweights[41] = incweights[41]/20
incweights = np.array(incweights)

# define necessary functions
def lognorm_pdf(xvals, mu, sigma):
    pdf_vals = sts.lognorm.pdf(xvals, s = sigma, scale = np.exp(mu))

    return pdf_vals

def ga_pdf(xvals, alpha, beta):
    pdf_vals = sts.gamma.pdf(xvals, alpha, loc=0, scale=beta)
    return pdf_vals

def inc_model_moments(param1, param2, distribution):
    if distribution == 'lognorm':
        mu, sigma = param1, param2
        xfx = lambda x: lognorm_pdf(x, mu, sigma)
    elif distribution == 'ga':
        alpha, beta = param1, param2
        xfx = lambda x: ga_pdf(x, alpha, beta)

    model_moments = []
    model_bins = list(incbins)
    model_bins[0] = 1e-10
    model_bins[42] = 1000 # arbitrary large number instead of inf to save time
    model_bins = np.array(model_bins)
    for i in range(1, 43):
        model_moments.append(intgr.quad(xfx, model_bins[i-1], model_bins[i])[0])
    return model_moments

def inc_err_vec(data, param1, param2, simple, distribution):
    moms_data = incweights.reshape(42,1)
    moms_model = np.array([inc_model_moments(param1, param2, distribution)]).reshape(42,1)
    if simple:
        err_vec = moms_model - moms_data
    else:
        err_vec = (moms_model - moms_data) / moms_data

    return err_vec

def inc_criterion(params, *args):
    param1, param2 = params
    data, W, dist = args
    err = inc_err_vec(data, param1, param2, simple=False, distribution=dist)
    crit_val = np.dot(np.dot(err.T, W), err)

    return crit_val
'''
--------------------------------------------------------------------
(a) Plot the histogram implied by the moments in the tab-delimited
text file usincmoms.txt.
--------------------------------------------------------------------
'''
if True:
    # plot the data
    n, bins, ignored = plt.hist(incvals, bins=incbins, weights=incweights)
    plt.title('Distribution of household income by selected income class, 2011', fontsize = 15)
    plt.xlabel('Household income ($1000)')
    plt.ylabel('Households (%)')
    plt.legend(loc='upper right')
    plt.xlim(0, 350)
    plt.ylim(0, 1.2*n.max())

    # save the plot
    output_path_1a = os.path.join(output_dir, 'fig_1a')
    plt.savefig(output_path_1a, bbox_inches = 'tight')

    plt.show()
    plt.close()
'''
--------------------------------------------------------------------
(b) Using GMM, fit the lognormal LN(x; mu, sigma) distribution defined
in the MLE notebook to the distribution of household income data using
the moments from the data file. Report your estimated values for
mu-hat and sigma-hat, as well as the value of the minimized criterion function.
Plot the histogram from part (a) overlayed with a line representing
the implied histogram from your estimated lognormal (LN) distribution.
--------------------------------------------------------------------
'''
# setup for optimizaiton
incvals0 = np.array(list(incvals))
incvals0[0] = 1e-10
W_hat0 = np.eye(42) # weight matrix is identiy matrix
inc_gmm_args_1b = (incvals0, W_hat0, 'lognorm')
lognorm_bounds = ((None, None), (1e-10, None))
mu0, sig0 = np.log(69677), 50.
params_1b = np.array([mu0, sig0])

if True:
    # optimization
    results_1b = opt.minimize(inc_criterion, params_1b, args=(inc_gmm_args_1b),
                            method='L-BFGS-B', bounds=lognorm_bounds) # solvers: L-BFGS-B, TNC, SQSLP
    # results
    mu_GMM_1b, sig_GMM_1b = results_1b.x
    print(results_1b)

if True:
    # report results
    print('Estimate of mu, if W = I: ', mu_GMM_1b, '\n',
        'Estimate of sigma, if W = I: ', sig_GMM_1b)
    print('Criterion function value, if W = I: ', results_1b.fun)

# inc_pts = np.linspace(0, 350, 1000)
lognorm_pts = inc_model_moments(mu_GMM_1b, sig_GMM_1b, 'lognorm')
lognorm_pts[40], lognorm_pts[41] = lognorm_pts[40]/10, lognorm_pts[41]/20
if True:
    # plot the results
    n, bins, ignored = plt.hist(incvals, bins=incbins, weights=incweights)
    plt.plot(incvals0, lognorm_pts, linewidth=2, color='r',
      label='$\mu$ GMM_1b = {}, $\sigma$ GMM_1b = {}'.format(mu_GMM_1b, sig_GMM_1b))
    plt.title('Distribution of household income by selected income class, 2011', fontsize = 15)
    plt.xlabel('Household income ($1000)')
    plt.ylabel('Households (%)')
    plt.legend(loc='upper right')
    plt.xlim(0, 350)
    plt.ylim(0, 1.2*n.max())

    # save the plot
    output_path_1b = os.path.join(output_dir, 'fig_1b')
    plt.savefig(output_path_1b, bbox_inches = 'tight')

    plt.show()
    plt.close()


'''
--------------------------------------------------------------------
(c) Using GMM, fit the gamma GA(x; alpha, beta) distribution defined in
the MLE notebook to the distribution of household income data using the
moments from the data file. Use alpha0 = 3 and beta0 = 20,000 as your initial
guess. Report your estimated values for alpha-hat and beta-hat, as well as
the value of the minimized criterion function. Use the same weighting
matrix as in part (b). Plot the histogram from part (a) overlayed with a
line representing the implied histogram from your estimated gamma (GA)
distribution.
--------------------------------------------------------------------
'''
# setup for optimizaiton
inc_gmm_args_1c = (incvals0, W_hat0, 'ga')
ga_bounds = ((1e-10, None), (1e-10, None))
alpha0, beta0= 3., 20.
params_1c = np.array([alpha0, beta0])

if True:
    # optimization
    results_1c = opt.minimize(inc_criterion, params_1c, args=(inc_gmm_args_1c),
                            method='L-BFGS-B', bounds=ga_bounds) # solvers: L-BFGS-B, TNC, SQSLP
    # results
    alpha_GMM_1c, beta_GMM_1c = results_1c.x
    print(results_1c)

ga_pts = inc_model_moments(alpha_GMM_1c, beta_GMM_1c, 'ga')
ga_pts[40], ga_pts[41] = ga_pts[40]/10, ga_pts[41]/20
if True:
    # plot the results
    n, bins, ignored = plt.hist(incvals, bins=incbins, weights=incweights)
    plt.plot(incvals0, ga_pts, linewidth=2, color='g',
      label='alpha GMM_1c = {}, beta GMM_1c = {}'.format(alpha_GMM_1c, beta_GMM_1c))
    plt.title('Distribution of household income by selected income class, 2011', fontsize = 15)
    plt.xlabel('Household income ($1000)')
    plt.ylabel('Households (%)')
    plt.legend(loc='upper right')
    plt.xlim(0, 350)
    plt.ylim(0, 1.2*n.max())

    # save the plot
    output_path_1c = os.path.join(output_dir, 'fig_1c')
    plt.savefig(output_path_1c, bbox_inches = 'tight')

    plt.show()
    plt.close()
'''
--------------------------------------------------------------------
(d) Plot the histogram from part (a) overlayed with the line representing
the implied histogram from your estimated lognormal (LN) distribution
from part (b) and the line representing the implied histogram from your
estimated gamma (GA) distribution from part (c). What is the most precise
way to tell which distribution fits the data the best? Which estimated
distribution--LN or GA--fits the data best?
--------------------------------------------------------------------
'''
if True:
    # plot the results
    n, bins, ignored = plt.hist(incvals, bins=incbins, weights=incweights)
    plt.plot(incvals0, lognorm_pts, linewidth=2, color='r',
      label='$\mu$ GMM_1b = {}, $\sigma$ GMM_1b = {}'.format(mu_GMM_1b, sig_GMM_1b))
    plt.plot(incvals0, ga_pts, linewidth=2, color='g',
      label='alpha GMM_1c = {}, beta GMM_1c = {}'.format(alpha_GMM_1c, beta_GMM_1c))
    plt.title('Distribution of household income by selected income class, 2011', fontsize = 15)
    plt.xlabel('Household income ($1000)')
    plt.ylabel('Households (%)')
    plt.legend(loc='upper right')
    plt.xlim(0, 350)
    plt.ylim(0, 1.2*n.max())

    # save the plot
    output_path_1d = os.path.join(output_dir, 'fig_1d')
    plt.savefig(output_path_1d, bbox_inches = 'tight')

    plt.show()
    plt.close()
'''
--------------------------------------------------------------------
(e) Repeat your estimation of the GA distribution from part (c),
but use the two-step estimator for the optimal weighting matrix.
Do your estimates for alpha and beta change much? How can you compare the
goodness of fit of this estimated distribution versus the goodness of fit of
the estimated distribution in part (c)?
--------------------------------------------------------------------
'''
# setup for optimizaiton with two-step W
inc_err = inc_err_vec(incmoms[0], alpha_GMM_1c, beta_GMM_1c, simple=False, distribution = 'ga')
VCV2 = np.dot(inc_err, inc_err.T) / np.array(incvals).shape[0]
W_hat2 = lin.pinv(VCV2)  # Use the pseudo-inverse calculated by SVD because VCV2 is ill-conditioned
inc_gmm_args_1e = (incvals0, W_hat2, 'ga')

if True:
    # optimization
    results_1e = opt.minimize(inc_criterion, params_1c, args=(inc_gmm_args_1e),
                            method='L-BFGS-B', bounds=ga_bounds) # solvers: L-BFGS-B, TNC, SQSLP
    # results
    alpha_GMM_1e, beta_GMM_1e = results_1e.x

if True:
    # report results
    print('Estimate of alpha, if W = I: ', alpha_GMM_1c, '\n',
        'Estimate of beta, if W = I: ', beta_GMM_1c)
    print('Estimate of alpha, if W = W_2step: ', alpha_GMM_1e, '\n',
        'Estimate of beta, if W = W_2step: ', beta_GMM_1e)
    print('Criterion function value, if W = I: ', results_1c.fun)
    print('Criterion function value, if W = W_2step: ', results_1e.fun)

ga_pts2 = inc_model_moments(alpha_GMM_1e, beta_GMM_1e, 'ga')
ga_pts2[40], ga_pts2[41] = ga_pts2[40]/10, ga_pts2[41]/20
if True:
    # plot the results
    n, bins, ignored = plt.hist(incvals, bins=incbins, weights=incweights)
    # plt.plot(incvals0, lognorm_pts, linewidth=2, color='r',
    #   label='$\mu$ GMM_1b = {}, $\sigma$ GMM_1b = {}'.format(mu_GMM_1b, sig_GMM_1b))
    plt.plot(incvals0, ga_pts, linewidth=2, color='g',
      label='alpha GMM_1c = {}, beta GMM_1c = {}'.format(alpha_GMM_1c, beta_GMM_1c))
    plt.plot(incvals0, ga_pts2, linewidth=2, color='b', linestyle='--',
      label='alpha GMM_1e = {}, beta GMM_1e = {}'.format(alpha_GMM_1e, beta_GMM_1e))
    plt.title('Distribution of household income by selected income class, 2011', fontsize = 15)
    plt.xlabel('Household income ($1000)')
    plt.ylabel('Households (%)')
    plt.legend(loc='upper right')
    plt.xlim(0, 350)
    plt.ylim(0, 1.2*n.max())

    # save the plot
    output_path_1e = os.path.join(output_dir, 'fig_1e')
    plt.savefig(output_path_1e, bbox_inches = 'tight')

    plt.show()
    plt.close()
