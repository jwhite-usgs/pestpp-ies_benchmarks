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
    exe_path = os.path.join(bin_path, "iwin", "ipestpp-ies.exe")
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
def write_empty_test_matrix():
    test_names = [t.split()[0] for t in tests.split('\n')]
    df = pd.DataFrame(index=test_names, columns=ies_vars)
    df.loc[:, "text"] = tests.split('\n')
    df.to_csv("ies_test.blank.csv")


def setup_suite_dir(model_d):
    pyemu.Ensemble.reseed()
    base_d = os.path.join(model_d, "template")
    new_d = os.path.join(model_d, "test_template")
    if os.path.exists(new_d):
        shutil.rmtree(new_d)
    shutil.copytree(base_d, new_d)
    print(platform.platform().lower())
    local=True
    if "linux" in platform.platform().lower() and "10par" in model_d:
        #print("travis_prep")
        #prep_for_travis(model_d)
        local=False
    pst = pyemu.Pst(os.path.join(new_d, "pest.pst"))
    print(pst.model_command)
    
    # set first par as fixed
    #pst.parameter_data.loc[pst.par_names[0], "partrans"] = "fixed"

    pst.observation_data.loc[pst.nnz_obs_names,"weight"] = 1.0

    # set noptmax
    pst.control_data.noptmax = noptmax

    # wipe all pestpp options
    pst.pestpp_options = {}

    # write a generic 2D cov
    if os.path.exists(os.path.join(new_d,"prior.jcb")):
        cov = pyemu.Cov.from_binary(os.path.join(new_d,"prior.jcb"))
        #cov.to_ascii(os.path.join(new_d,"prior.cov"))
    elif os.path.exists(os.path.join(new_d, "prior.cov")):
        cov = pyemu.Cov.from_ascii(os.path.join(new_d, "prior.cov"))
    else:
        cov = pyemu.Cov.from_parameter_data(pst)
        cov = pyemu.Cov(cov.as_2d, names=cov.row_names)
        #cov.to_ascii(os.path.join(new_d, "prior.cov"))
        cov.to_binary(os.path.join(new_d, "prior.jcb"))

    # draw some ensembles
    idx = [i for i in range(num_reals)]
    idx[-1] = "base"
    pe = pyemu.ParameterEnsemble.from_gaussian_draw(pst, cov=cov, num_reals=num_reals,
                                                    use_homegrown=True,group_chunks=True)
    pe.index = idx
    pe.to_csv(os.path.join(new_d, "par.csv"))
    pe.to_binary(os.path.join(new_d, "par.jcb"))
    pe.to_csv(os.path.join(new_d, "sweep_in.csv"))
    pe.loc[:, pst.adj_par_names].to_csv(os.path.join(new_d, "par_some.csv"))
    pe.iloc[:-3, :].to_csv(os.path.join(new_d, "restart_failed_par.csv"))
    oe = pyemu.ObservationEnsemble.from_id_gaussian_draw(pst, num_reals=num_reals)
    oe.index = idx
    oe.to_csv(os.path.join(new_d, "obs.csv"))
    oe.iloc[:-3, :].to_csv(os.path.join(new_d, "restart_failed_base_obs.csv"))
    oe.to_binary(os.path.join(new_d, "obs.jcb"))

    pst.write(os.path.join(new_d, "pest.pst"))
    # run sweep
    m_d = os.path.join(model_d,"master_sweep1")
    if os.path.exists(m_d):
        shutil.rmtree(m_d)
    pyemu.os_utils.start_workers(new_d, exe_path.replace("-ies","-swp"), "pest.pst", 5, master_dir=m_d,
                           slave_root=model_d,local=local,port=port)
    #shutil.copytree(new_d,m_d)
    #pyemu.os_utils.run("{0} pest.pst".format(exe_path.replace("-ies","-swp")),cwd=m_d)

    # process sweep output as restart csv and jcb
    df = pd.read_csv(os.path.join(m_d, "sweep_out.csv"),index_col=0)
    df.index = df.input_run_id
    df.columns = [c.lower() for c in df.columns]
    df.to_csv(os.path.join(new_d, "restart.csv"))
    df = df.loc[:, pst.nnz_obs_names]
    df.loc[:, pst.nnz_obs_names].to_csv(os.path.join(new_d, "restart_some.csv"))
    df.iloc[:-3, :].to_csv(os.path.join(new_d, "restart_failed.csv"))

    # run pyemu ies
    # pyemu_d = os.path.join(model_d, "master_pyemu")
    # if os.path.exists(pyemu_d):
    #     shutil.rmtree(pyemu_d)
    # shutil.copytree(new_d, pyemu_d)
    # bdir = os.getcwd()
    # os.chdir(pyemu_d)
    # ies = pyemu.EnsembleSmoother("pest.pst", num_slaves=10, verbose="ies.log", slave_dir=os.path.join("..", "template"))
    # ies.initialize(parensemble="par.csv", obsensemble="obs.csv")
    # for i in range(pst.control_data.noptmax):
    #     ies.update()
    # os.chdir(bdir)

    # pestpp_d = os.path.join(model_d,"master")
    # if os.path.exists(pestpp_d):
    #     shutil.rmtree(pestpp_d)
    # shutil.copytree(new_d,pestpp_d)


def run_suite(model_d,silent_master=False):
    df = pd.read_csv("ies_test.csv")
    df = df.loc[df.text.apply(lambda x: model_d in x), :]
    df.fillna('', inplace=True)
    print(df)
    #model_d = "ies_10par_xsec"
    template_d = os.path.join(model_d, "test_template")

    pst = pyemu.Pst(os.path.join(template_d, "pest.pst"))
    errors = []
    should_compare = []
    for i in range(df.shape[0]):

    #for i in range(3,4):
    
        test_vars = df.iloc[i, :].to_dict()
        # if test_vars["pyemu_compare"] == 0:
        #     continue
        test_name = test_vars["text"].split()[0].replace(")", '')
        print(test_vars["text"])
        #if "6" not in test_vars["text"]:
        #    continue
        compare = False
        try:
            pst.pestpp_options = {}
            for v in ies_vars:
                if pd.notnull(test_vars[v]):
                    try:
                        pst.pestpp_options[v] = test_vars[v].replace('"','')
                    except:
                        pst.pestpp_options[v] = test_vars[v]

            pst.pestpp_options["ies_num_reals"] = 30
            pst.pestpp_options["ies_group_draws"] = False
            tags = ["par_en","parameter_ensemble"]
            for tag in tags:
                if (tag in pst.pestpp_options and len(pst.pestpp_options[tag]) > 0):
                    compare = True

            pst.write(os.path.join(template_d, "pest.pst"))
            test_d = os.path.join(model_d, "master_test_{0}".format(test_name))
            if compare:
                should_compare.append(test_d)
            if os.path.exists(test_d):
                try:
                    shutil.rmtree(test_d)
                except:
                    print("error removing existing test_d: {0}".format(test_d))
                    continue
            pyemu.os_utils.start_workers(template_d, exe_path, "pest.pst", num_slaves=15,
                                       master_dir=test_d, verbose=True, slave_root=model_d,
                                       silent_master=silent_master,port=port)
        except Exception as e:
            errors.append("error:"+test_vars["text"]+" "+str(e))
    if len(errors) > 0:
        raise Exception("\n".join(errors))
    return should_compare

def compare_suite(model_d,should_compare=None):
    base_d = os.path.join(model_d, "baseline_opt")
    test_ds = [d for d in os.listdir(model_d) if "master_test" in d and not "3b" in d]
    errors = []
    for test_d in test_ds:
        test_d = os.path.join(model_d, test_d)
        if should_compare is not None and test_d not in should_compare:
            print("skipping dir {0}".format(test_d))
            continue
        for compare_file in compare_files:
            if not os.path.exists(os.path.join(test_d, compare_file)):
                errors.append("missing compare file '{0}' in test_d '{1}'".format(compare_file, test_d))
            else:
                base_file = os.path.join(base_d, "{0}__{1}".
                                         format(os.path.split(test_d)[-1], compare_file))
                test_file = os.path.join(test_d, compare_file)
                try:
                    base_df = pd.read_csv(base_file,index_col=0)
                except Exception as e:
                    errors.append("error loading base_file {0}: {1}".format(base_file, str(e)))
                    continue
                try:
                    test_df = pd.read_csv(test_file,index_col=0)
                except Exception as e:
                    errors.append("error loading test_file {0}, {1}: {2}".format(test_d, base_file, str(e)))
                    continue
                try:
                    diff = (test_df - base_df).apply(np.abs)
                except Exception as e:
                    errors.append("error differencing base and test for '{0}':{1}".format(base_file, str(e)))
                max_diff = diff.max().max()
                if max_diff > diff_tol:
                    errors.append("max diff greater than diff tol for '{0}':{1}".format(base_file, max_diff))
    if len(errors) > 0:
        for e in errors:
            print("ERROR: ", e)
        raise Exception("errors in {0}: ".format(model_d) + '\n'.join(errors))


def test_10par_xsec(silent_master=False):
    should_compare = run_suite("ies_10par_xsec",silent_master=silent_master)
    compare_suite("ies_10par_xsec",should_compare)


def test_freyberg():
    should_compare = run_suite("ies_freyberg")
    compare_suite("ies_freyberg",should_compare)


def rebase(model_d):
    """reset the "base" for the standard test suite"""
    # run_suite(model_d)
    base_d = os.path.join(model_d, "baseline_opt")
    if os.path.exists(base_d):
        shutil.rmtree(base_d)
    os.mkdir(base_d)

    # find test dirs
    print(os.listdir(model_d))
    test_ds = [d for d in os.listdir(model_d) if "master_test" in d]
    for test_d in test_ds:
        test_d = os.path.join(model_d, test_d)
        rec_file = os.path.join(test_d,"pest.rec")
        if not os.path.exists(rec_file):
            print("WARNING rec file {0} not found".format(rec_file))
        else:
            shutil.copy2(rec_file,os.path.join(base_d, "{0}__{1}".format(os.path.split(test_d)[-1], "pest.rec")))
        for compare_file in compare_files:
            if not os.path.exists(os.path.join(test_d, compare_file)):
                print("WARNING missing compare file:", test_d, compare_file)
            else:
                shutil.copy2(os.path.join(test_d, compare_file),
                             os.path.join(base_d, "{0}__{1}".
                                          format(os.path.split(test_d)[-1], compare_file)))



if __name__ == "__main__":

    #setup_suite_dir("ies_10par_xsec")
    #setup_suite_dir("ies_freyberg")
    #run_suite("ies_10par_xsec")
    #run_suite("ies_freyberg")
    #rebase("ies_10par_xsec")
    #rebase("ies_freyberg")

    #compare_suite("ies_10par_xsec")
    #compare_suite("ies_freyberg")
    test_freyberg()
    test_10par_xsec()

    