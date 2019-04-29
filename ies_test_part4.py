# TODO: test variance and mean of draws, add chenoliver and test approx and full solution
import os
import shutil
import platform
import numpy as np
import pandas as pd
import platform
import matplotlib.pyplot as plt
import pyemu

tests = """0) 10par_xsec "standard user mode" - draw reals from par-bounds prior and obs noise from weights
0a) 10par_xsec same as 0) but with multple lambda 
1) 10par_xsec start with existing par csv and obs csv - using empirical parcov and obscov
1a) 10par_xsec start with existing par csv and obs csv - using parcov file
2) 10par_xsec start with existing par csv and drawing obs en from weights 
3) 10par_xsec restart with full simulated obs en
3a) 10par_xsec restart with failed runs in simulated obs en
3b) 10par_xsec restart with failed runs and bad phi runs in simulated obs en with multiple lam
4) 10par_xsec reg_factor = 0.5 test
5)  10par_xsec full solution test with standard draw mode
5a) 10par_xsec full solution test with empirical parcov
6) freyberg "standard user mode" - draw reals from par-bounds prior and obs noise from weights
6a) freyberg same as 0) but with multple lambda 
7) freyberg draw par en from full parcov supplied in file
8) freyberg full solution with empirical parcov - supplied par csv, obs csv and restart csv with fails, bad phi,MAP solution, prior scaling, lam mults 
9) synth restart and upgrade 1.1M par problem"""

ies_vars = ["ies_par_en", "ies_obs_en", "ies_restart_obs_en",
            "ies_bad_phi", "parcov_filename", "ies_num_reals",
            "ies_use_approx", "ies_use_prior_scaling", "ies_reg_factor",
            "ies_lambda_mults", "ies_initial_lambda","ies_include_base","ies_subset_size"]


# the old path system before moving to separate benchmarks repo
# intel = False
# if "windows" in platform.platform().lower():
#     if intel:
#         exe_path = os.path.join("..", "..", "..", "bin", "iwin", "ipestpp-ies.exe")
#     else:
#         exe_path = os.path.join("..", "..", "..", "bin", "win", "pestpp-ies.exe")
# elif "darwin" in platform.platform().lower():
#     exe_path = os.path.join("..", "..", "..", "bin", "mac", "pestpp-ies")
# else:
#     exe_path = os.path.join("..", "..", "..", "bin", "linux", "pestpp-ies")

bin_path = os.path.join("test_bin")
if "linux" in platform.platform().lower():
    bin_path = os.path.join(bin_path,"linux")
elif "darwin" in platform.platform().lower():
    bin_path = os.path.join(bin_path,"mac")
else:
    bin_path = os.path.join(bin_path,"win")

bin_path = os.path.abspath("test_bin")
os.environ["PATH"] += os.pathsep + bin_path

# case of either appveyor, travis or local
if os.path.exists(os.path.join("pestpp","bin")):
    bin_path = os.path.join("..","..","pestpp","bin")
else:
    bin_path = os.path.join("..","..","..","..","pestpp","bin")

        
if "windows" in platform.platform().lower():
    exe_path = os.path.join(bin_path, "win", "pestpp-ies.exe")
elif "darwin" in platform.platform().lower():
    exe_path = os.path.join(bin_path,  "mac", "pestpp-ies")
else:
    exe_path = os.path.join(bin_path, "linux", "pestpp-ies")



noptmax = 3

compare_files = ["pest.phi.actual.csv", "pest.phi.meas.csv", "pest.phi.regul.csv",
                 "pest.{0}.par.csv".format(noptmax), "pest.{0}.obs.csv".format(noptmax),
                 "pest.{0}.par.csv".format(0), "pest.base.obs.csv"]
diff_tol = 1.0e-6
port = 4016
num_reals = 10


def tenpar_xsec_aal_sigma_dist_test():
    """testing what happens with really large sigma dist for aal"""

    model_d = "ies_10par_xsec"
    test_d = os.path.join(model_d, "master_aal_sigma_dist_test")
    template_d = os.path.join(model_d, "test_template")

    if not os.path.exists(template_d):
        raise Exception("template_d {0} not found".format(template_d))
    pst_name = os.path.join(template_d, "pest.pst")
    pst = pyemu.Pst(pst_name)
    
    if os.path.exists(test_d):
        shutil.rmtree(test_d)
    shutil.copytree(template_d, test_d)
    pst.pestpp_options = {}
    pst.pestpp_options["ies_num_reals"] = 50
    pst.pestpp_options["ies_autoadaloc_sigma_dist"] = 2.0
    pst.pestpp_options["ies_autoadaloc"] = True
    pst.pestpp_options["ies_verbose_level"] = 2
    pst.control_data.noptmax = 1
    pst.write(os.path.join(template_d, "pest_aal_sigma_dist.pst"))
    pyemu.os_utils.start_slaves(template_d, exe_path, "pest_aal_sigma_dist.pst", num_slaves=10,
                                master_dir=test_d, verbose=True, slave_root=model_d,
                                port=port)
    
    df = pd.read_csv(os.path.join(test_d,"pest_aal_sigma_dist.1.autoadaloc.csv"))
    df.loc[:,"parnme"] = df.parnme.str.lower()
    df.loc[:, "obsnme"] = df.obsnme.str.lower()
    print(df.iloc[0,:])
    
    # fig,axes = plt.subplots(pst.npar_adj,pst.nnz_obs,figsize=(6.5,11))

    # for i,pname in enumerate(pst.adj_par_names):
    #     for j,oname in enumerate(pst.nnz_obs_names):
    #         ddf = df.loc[df.apply(lambda x: x.parnme==pname and x.obsnme==oname,axis=1),:].iloc[0,:]
    #         ax = axes[i,j]
    #         print(ddf.iloc[6:])
    #         ddf.iloc[6:].apply(np.float).hist(ax=ax,bins=10,facecolor='b',alpha=0.5)
    #         ylim = ax.get_ylim()
    #         ylim = [0,ylim[1]*1.5]
    #         ax.plot([ddf.loc["correlation_coeff"],ddf.loc["correlation_coeff"]],ylim,"r",label="estimate")
    #         mn,std = ddf.loc["background_mean"], ddf.loc["background_stdev"]
    #         ax.plot([mn,mn],ylim,"b-", label="bg mean")
    #         for m,c in zip([1,2,3],["--","-.",":"]):
    #             ax.plot([mn+(m*std),mn+(m*std)],ylim,color="b",ls=c,label="{0} bg std".format(m))
    #             ax.plot([mn - (m * std), mn - (m * std)], ylim, color="b",ls=c)
    #         ax.grid()
    #         ax.set_ylim(ylim)
    #         ax.set_xlim(-1,1)
    #         ax.set_yticks([])
    #         kept = bool(ddf.loc["kept"])
    #         ax.set_title("{0} - {1}, kept: {2}".format(pname,oname,kept),loc="left")
    # ax.legend()
    # plt.tight_layout()
    # plt.savefig("aal_10par_2sigma.pdf")
    # plt.show()




def tenpar_xsec_aal_invest():
    model_d = "ies_10par_xsec"
    test_d = os.path.join(model_d, "master_aal_test")
    template_d = os.path.join(model_d, "test_template")

    if not os.path.exists(template_d):
        raise Exception("template_d {0} not found".format(template_d))
    pst_name = os.path.join(template_d, "pest.pst")
    pst = pyemu.Pst(pst_name)

    if os.path.exists(test_d):
       shutil.rmtree(test_d)
    shutil.copytree(template_d, test_d)
    pst.pestpp_options = {}
    pst.pestpp_options["ies_num_reals"] = 100
    pst.pestpp_options["ies_lambda_mults"] = 0.0000001
    pst.pestpp_options["lambda_scale_fac"] = 0.00001
    #pst.pestpp_options["ies_autoadaloc"] = True
    pe = pyemu.ParameterEnsemble.from_gaussian_draw(pst=pst,cov=pyemu.Cov.from_parameter_data(pst),num_reals=100)
    pe.loc[:,pst.adj_par_names[:2]] = pst.parameter_data.loc[pst.adj_par_names[0],"parlbnd"]

    pe.to_csv(os.path.join(template_d,"bound_par.csv"))
    pst.pestpp_options["ies_par_en"] = "bound_par.csv"
    pst.pestpp_options["ies_enforce_bounds"] = False
    pst.pestpp_options["ies_verbose_level"] = 3
    pst.control_data.noptmax = 1
    pst.write(os.path.join(template_d, "pest_aal.pst"))
    pyemu.os_utils.start_slaves(template_d, exe_path, "pest_aal.pst", num_slaves=30,
                                master_dir=test_d, verbose=True, slave_root=model_d,
                                port=port)


    # pst.pestpp_options = {}
    # pst.control_data.noptmax = -1
    # pst.write(os.path.join(test_d, "pest_aal_jco.pst"))
    # pyemu.os_utils.run("{0} pest_aal_jco.pst".format(exe_path.replace("-ies","-glm")),cwd=test_d)

    #df = pd.read_csv(os.path.join(test_d,"pest_aal."))


def tenpar_base_run_test():
    model_d = "ies_10par_xsec"
    test_d = os.path.join(model_d, "master_base_test")
    template_d = os.path.join(model_d, "test_template")

    if not os.path.exists(template_d):
        raise Exception("template_d {0} not found".format(template_d))
    pst_name = os.path.join(template_d, "pest.pst")
    pst = pyemu.Pst(pst_name)
    pst.pestpp_options = {}
    pst.pestpp_options["ies_num_reals"] = 10
    pst.pestpp_options["ies_include_base"] = True
    pst.control_data.noptmax = -1

    pst.write(os.path.join(template_d,"pest_base.pst"))
    if os.path.exists(test_d):
        shutil.rmtree(test_d)
    shutil.copytree(template_d,test_d)
    pyemu.os_utils.run("{0} pest_base.pst".format(exe_path),cwd=test_d)

    pst.control_data.noptmax = 0
    pst.write(os.path.join(template_d, "pest_base.pst"))
    pyemu.os_utils.run("{0} pest_base.pst".format(exe_path.replace("-ies","-glm")), cwd=test_d)

    oe = pd.read_csv(os.path.join(test_d,"pest_base.0.obs.csv"),index_col=0)
    pst = pyemu.Pst(os.path.join(test_d,"pest_base.pst"))
    print(oe.loc["base",:])
    print(pst.res.modelled)
    d = oe.loc["base",:] - pst.res.modelled
    assert d.sum() == 0.0,d


def tenpar_xsec_combined_autoadaloc_test():
    """testing combined matrix + autoadaloc"""
    model_d = "ies_10par_xsec"
    test_d = os.path.join(model_d, "master_comb_aal_test1")
    template_d = os.path.join(model_d, "test_template")

    if not os.path.exists(template_d):
        raise Exception("template_d {0} not found".format(template_d))
    pst_name = os.path.join(template_d, "pest.pst")
    pst = pyemu.Pst(pst_name)

    if os.path.exists(test_d):
       shutil.rmtree(test_d)
    shutil.copytree(template_d, test_d)
    pst.pestpp_options = {}
    pst.pestpp_options["ies_num_reals"] = 50
    pst.control_data.noptmax = -1
    pst.write(os.path.join(template_d,"pest_aal.pst"))
    pyemu.os_utils.start_slaves(template_d, exe_path, "pest_aal.pst", num_slaves=10,
                               master_dir=test_d, verbose=True, slave_root=model_d,
                               port=port)

    mat = pyemu.Matrix.from_names(pst.nnz_obs_names,pst.adj_par_names).to_dataframe()
    mat.loc[:,:] = 1
    mat.loc[:,pst.adj_par_names[::2]] = 0
    pyemu.Matrix.from_dataframe(mat).to_ascii(os.path.join(template_d,"loc.mat"))

    pst.pestpp_options["ies_localizer"] = "loc.mat"
    pst.pestpp_options["ies_par_en"] = "pest_aal.0.par.csv"
    pst.pestpp_options["ies_obs_en"] = "pest_aal.base.obs.csv"
    pst.pestpp_options["ies_restart_obs_en"] = "pest_aal.0.obs.csv"
    pst.pestpp_options["ies_autoadaloc"] = True
    pst.pestpp_options["ies_verbose_level"] = 3
    pst.control_data.noptmax = 1

    pe = pyemu.ParameterEnsemble.from_dataframe(df=pd.read_csv(os.path.join(test_d, "pest_aal.0.par.csv"), index_col=0),
                                                pst=pst)

    oe = pyemu.ObservationEnsemble.from_dataframe(
        df=pd.read_csv(os.path.join(test_d, "pest_aal.0.obs.csv"), index_col=0), pst=pst)

    for f in ["pest_aal.0.par.csv","pest_aal.base.obs.csv","pest_aal.0.obs.csv"]:
        shutil.copy2(os.path.join(test_d,f),os.path.join(template_d,f))




    pst.write(os.path.join(template_d, "pest_aal_restart.pst"))
    pyemu.os_utils.start_slaves(template_d, exe_path, "pest_aal_restart.pst", num_slaves=10,
                                master_dir=test_d, verbose=True, slave_root=model_d,
                                port=port)
    df = pyemu.Matrix.from_ascii(os.path.join(test_d,"pest_aal_restart.1.autoadaloc.tCC.mat")).to_dataframe()
    print(df.loc[:,pst.adj_par_names[::2]].sum())
    pe2 = pd.read_csv(os.path.join(test_d,"pest_aal_restart.0.par.csv"))
    diff = pe - pe2
    print(diff.loc[:,pst.adj_par_names[::2]].sum())
    assert df.loc[:,pst.adj_par_names[::2]].sum().sum() == 0.0
    assert diff.loc[:,pst.adj_par_names[::2]].sum().sum() == 0.0

def freyberg_aal_test():
    import flopy
    model_d = "ies_freyberg"
    test_d = os.path.join(model_d, "master_aal_test")
    template_d = os.path.join(model_d, "template")
    m = flopy.modflow.Modflow.load("freyberg.nam",model_ws=template_d,load_only=[],check=False)
    if os.path.exists(test_d):
       shutil.rmtree(test_d)
    # print("loading pst")
    pst = pyemu.Pst(os.path.join(template_d, "pest.pst"))

    par = pst.parameter_data

    pst.pestpp_options = {}
    pst.pestpp_options["ies_num_reals"] = 100
    pst.pestpp_options["ies_subset_size"] = 100
    pst.pestpp_options["ies_num_threads"] = 20
    pst.pestpp_options["ies_lambda_mults"] = [1.0]
    pst.pestpp_options["lambda_scale_fac"] = 1.0
    #pst.pestpp_options["ies_include_base"] = False
    #pst.pestpp_options["ies_par_en"] = "par_local.csv"
    pst.pestpp_options["ies_use_approx"] = False
    pst.pestpp_options["ies_use_prior_scaling"] = True
    #pst.pestpp_options["ies_localizer"] = "localizer.mat"
    pst.pestpp_options["ies_localize_how"] = "par"
    pst.pestpp_options["ies_verbose_level"] = 2
    pst.pestpp_options["ies_save_lambda_en"] = True
    pst.pestpp_options["ies_subset_how"] = "random"
    pst.pestpp_options["ies_accept_phi_fac"] = 1000.0
    pst.pestpp_options["overdue_giveup_fac"] = 10.0
    pst.pestpp_options["ies_autoadaloc"] = True
    pst.pestpp_options["ies_autoadaloc_sigma_dist"] = 1.0
    pst.control_data.noptmax = 1
    pst.write(os.path.join(template_d, "pest_aal.pst"))
    pyemu.os_utils.start_slaves(template_d, exe_path, "pest_aal.pst", num_slaves=30, master_dir=test_d,
                               slave_root=model_d,port=port)

def freyberg_aal_invest():
    import flopy
    model_d = "ies_freyberg"
    test_d = os.path.join(model_d, "master_aal_glm_jco")
    template_d = os.path.join(model_d, "template")
    jco_file = os.path.join(test_d,"pest_aal_jco.jcb")
    if not os.path.exists(jco_file):
        pst = pyemu.Pst(os.path.join(template_d, "pest.pst"))
        pst.control_data.noptmax = -1
        pst.write(os.path.join(template_d, "pest_aal_jco.pst"))
        pyemu.os_utils.start_slaves(template_d, exe_path.replace("-ies", "-glm"), "pest_aal_jco.pst", 30,
                                    slave_root=model_d, master_dir=test_d, port=port,verbose=True)
    jco = pyemu.Jco.from_binary(jco_file).to_dataframe()

    test_d = os.path.join(model_d,"master_aal_test")
    m = flopy.modflow.Modflow.load("freyberg.nam", model_ws=template_d, load_only=[], check=False)
    tcc = pyemu.Matrix.from_ascii(os.path.join(test_d,"pest_aal.1.autoadaloc.tCC.mat")).to_dataframe()
    pnames = pd.DataFrame({"name":tcc.columns.values})
    pnames.loc[:,"i"] = pnames.name.apply(lambda x: int(x.split('_')[1][1:]))
    pnames.loc[:,"j"] = pnames.name.apply(lambda x: int(x.split('_')[2][1:]))
    pdict = {n:(i,j) for n,i,j in zip(pnames.name,pnames.i,pnames.j)}
    from matplotlib.backends.backend_pdf import PdfPages
    with PdfPages(os.path.join(test_d,"compare_sens_cc.pdf")) as pdf:
        for obs in tcc.index:
            if not obs.startswith("c00"):
                continue
            i = int(obs[6:8])
            j = int(obs[9:11])
            tcc_obs = tcc.loc[obs,:].apply(np.abs)
            jco_obs = jco.loc[obs,:].apply(np.abs)
            print(tcc_obs)
            arr_cc = np.zeros((m.nrow,m.ncol))
            arr_jco = np.zeros((m.nrow, m.ncol))
            for n,v in zip(tcc_obs.index,tcc_obs.values):
                if not "hk" in n:
                    continue
                arr_cc[pdict[n][0],pdict[n][1]] = v
                arr_jco[pdict[n][0], pdict[n][1]] = jco_obs[n]
            fig = plt.figure(figsize=(10,10))

            ax = plt.subplot(121,aspect="equal")
            ax2 = plt.subplot(122, aspect="equal")
            arr_cc = np.ma.masked_where(arr_cc<1.0e-6,arr_cc)
            arr_jco = np.ma.masked_where(arr_jco<1.0e-6, arr_jco)
            arr_cc = arr_cc / arr_cc.max()
            arr_jco = arr_jco / arr_jco.max()
            c = ax.pcolormesh(m.sr.xcentergrid,m.sr.ycentergrid,arr_cc,alpha=0.5,vmin=0,vmax=1)
            plt.colorbar(c,ax=ax)
            c2 = ax2.pcolormesh(m.sr.xcentergrid, m.sr.ycentergrid, arr_jco, alpha=0.5,vmin=0,vmax=1)
            plt.colorbar(c2,ax=ax2)
            ax.scatter([m.sr.xcentergrid[i,j]],[m.sr.ycentergrid[i,j]],marker='.',s=50)
            ax2.scatter([m.sr.xcentergrid[i, j]], [m.sr.ycentergrid[i, j]], marker='.', s=50)
            ax.set_title(obs)
            pdf.savefig()
            plt.close(fig)


def tenpar_high_phi_test():
    model_d = "ies_10par_xsec"
    test_d = os.path.join(model_d, "master_high_phi_test")
    template_d = os.path.join(model_d, "test_template")

    if not os.path.exists(template_d):
        raise Exception("template_d {0} not found".format(template_d))
    pst_name = os.path.join(template_d, "pest.pst")
    pst = pyemu.Pst(pst_name)

    if os.path.exists(test_d):
       shutil.rmtree(test_d)
    #shutil.copytree(template_d, test_d)
    pst.pestpp_options = {}
    pst.pestpp_options["ies_num_reals"] = 10
    pst.pestpp_options["ies_lambda_mults"] = 1.0
    pst.pestpp_options["lambda_scale_fac"] = [0.9,1.0]
    pst.pestpp_options['ies_subset_size'] = 10
    pst.pestpp_options["ies_debug_high_subset_phi"] =True
    pst.control_data.noptmax = 1
    pst.write(os.path.join(template_d,"pest_high_phi.pst"))
    pyemu.os_utils.start_slaves(template_d, exe_path, "pest_high_phi.pst", num_slaves=10,
                               master_dir=test_d, verbose=True, slave_root=model_d,
                               port=port)
    phi1 = pd.read_csv(os.path.join(test_d,"pest_high_phi.phi.actual.csv"),index_col=0)
    pst.pestpp_options = {}
    pst.pestpp_options["ies_num_reals"] = 10
    pst.pestpp_options["ies_lambda_mults"] = 1.0
    pst.pestpp_options["lambda_scale_fac"] = [0.9,1.0]
    pst.pestpp_options['ies_subset_size'] = 10
    #pst.pestpp_options["ies_debug_high_subset_phi"] =True
    pst.control_data.noptmax = 1
    pst.write(os.path.join(template_d,"pest_high_phi.pst"))
    pyemu.os_utils.start_slaves(template_d, exe_path, "pest_high_phi.pst", num_slaves=10,
                               master_dir=test_d, verbose=True, slave_root=model_d,
                               port=port)
    phi2 = pd.read_csv(os.path.join(test_d,"pest_high_phi.phi.actual.csv"),index_col=0)
    diff = phi1 - phi2
    assert diff.max().max() == 0.0

    pst.pestpp_options = {}
    pst.pestpp_options["ies_num_reals"] = 10
    pst.pestpp_options["ies_lambda_mults"] = 1.0
    pst.pestpp_options["lambda_scale_fac"] = [0.9,1.0]
    pst.pestpp_options['ies_subset_size'] = 10
    pst.pestpp_options["ies_debug_high_upgrade_phi"] =True
    pst.control_data.noptmax = 1
    pst.write(os.path.join(template_d,"pest_high_phi.pst"))
    pyemu.os_utils.start_slaves(template_d, exe_path, "pest_high_phi.pst", num_slaves=10,
                               master_dir=test_d, verbose=True, slave_root=model_d,
                               port=port)
    phi3 = pd.read_csv(os.path.join(test_d,"pest_high_phi.phi.actual.csv"),index_col=0)
    diff = phi3 - phi2
    assert diff.max().max() == 0.0

    pst.pestpp_options = {}
    pst.pestpp_options["ies_num_reals"] = 10
    pst.pestpp_options["ies_lambda_mults"] = [0.5,1.0]
    pst.pestpp_options["lambda_scale_fac"] = [0.9,1.0]
    pst.pestpp_options['ies_subset_size'] = 3
    pst.pestpp_options["ies_debug_high_upgrade_phi"] = True
    pst.pestpp_options["ies_debug_fail_subset"] = True
    pst.pestpp_options["ies_debug_fail_remainder"] = True
    pst.pestpp_options["ies_debug_bad_phi"] = True
    pst.control_data.noptmax = 3
    pst.write(os.path.join(template_d,"pest_high_phi.pst"))
    pyemu.os_utils.start_slaves(template_d, exe_path, "pest_high_phi.pst", num_slaves=10,
                               master_dir=test_d, verbose=True, slave_root=model_d,
                               port=port)
    phi4 = pd.read_csv(os.path.join(test_d,"pest_high_phi.phi.actual.csv"),index_col=0)
    assert os.path.exists(os.path.join(test_d,"pest_high_phi.3.obs.csv"))

    pst.pestpp_options = {}
    pst.pestpp_options["ies_num_reals"] = 10
    pst.pestpp_options["ies_lambda_mults"] = [0.5,1.0]
    pst.pestpp_options["lambda_scale_fac"] = [0.9,1.0]
    pst.pestpp_options['ies_subset_size'] = 3
    pst.pestpp_options["ies_debug_high_subset_phi"] = True
    pst.pestpp_options["ies_debug_fail_subset"] = True
    pst.pestpp_options["ies_debug_fail_remainder"] = True
    pst.pestpp_options["ies_debug_bad_phi"] = True
    pst.control_data.noptmax = 3
    pst.write(os.path.join(template_d,"pest_high_phi.pst"))
    pyemu.os_utils.start_slaves(template_d, exe_path, "pest_high_phi.pst", num_slaves=10,
                               master_dir=test_d, verbose=True, slave_root=model_d,
                               port=port)
    phi5 = pd.read_csv(os.path.join(test_d,"pest_high_phi.phi.actual.csv"),index_col=0)
    assert os.path.exists(os.path.join(test_d,"pest_high_phi.3.obs.csv"))
    

if __name__ == "__main__":
    #tenpar_base_run_test()
    #tenpar_xsec_autoadaloc_test()
    #tenpar_xsec_combined_autoadaloc_test()
    #tenpar_xsec_aal_sigma_dist_test()
    #tenpar_by_vars_test()
    #tenpar_xsec_aal_invest()
    #temp()
    #tenpar_localize_how_test()
    #clues_longnames_test()
    #freyberg_local_threads_test()
    #freyberg_aal_test()
    tenpar_high_phi_test()