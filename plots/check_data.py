import numpy as np
import pandas as pd
import json
with open("main_data.json","r") as f:
    rs = json.load(f)
t = pd.DataFrame(rs) 
t = t[~t.experiment.str.contains("dyn__with_static")]
t = t[~t.experiment.str.contains("binning_comparison")]
for n in [500,1000,2000,3000]:
    exps = t[t.n==n].experiment.unique()
    ls_all_exps = ["dynamic_theory", "static", "dynamic", "dynamic_with_static"]
    ls_all_exps += ["binning_with_dyn_start", "binning_with_dyn_middle", "binning_with_dyn_end"]
    n_bins = int(np.ceil(np.log2(n)))
    ls_all_exps += [f"binning_with_defaults{i}" for i in range(n_bins)]
    ls_all_exps += [f"binning_no_defaults{i}" for i in range(n_bins)]
    if n==500:
        ls_all_exps += ["binning_no_defaults_sc5"]
    elif n==1000:
        ls_all_exps += ["binning_no_defaults_sc6"]
    if n in [500, 1000]:
        ls_all_exps += ["binning_with_dp_start", "binning_with_dp_middle", "binning_with_dp_end"]
    
    missing_exps = list(set(ls_all_exps) - set(exps))
    missing_exps.sort()
    if len(missing_exps)>0:
        print(f"\nMissing exps for n={n}:\n")
        print("\n".join(missing_exps))
