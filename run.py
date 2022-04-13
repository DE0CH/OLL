from onell_algs import OneMax, LeadingOne
from onell_algs import onell_static, onell_dynamic_5params, onell_dynamic_5params_old, onell_dynamic_theory, onell_lbd_one, rls_optimal_lo, rls
import numpy as np
import argparse

alg_dict = {
    "stat_4params": {'func': onell_static, 'params':None},
    "dyn_5params": {'func': onell_dynamic_5params, 'params': None},
    "dyn_theory": {'func': onell_dynamic_theory, 'params': None},
    "dyn_onefifth": {'func': onell_dynamic_5params, 'params': 'alpha=1,beta=1,gamma=1,A=1.107,b=0.67'},
    "lbd_one": {'func': onell_lbd_one, 'params': None},
    "rls_lo": {'func': rls_optimal_lo, 'params': None},
    "rls": {'func': rls, 'params': None}
}

def static(n, seed, params):
    onell_static()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int,required=True)
    parser.add_argument("--alg", default="stat_4params", choices=alg_dict.keys())
    parser.add_argument("--seed", type=int, default=0)    
    parser.add_argument("--max_evals", type=int, default=500000)
    parser.add_argument("--problem",default="OM")
    args = parser.parse_args()

    if args.problem == "OM":
        problem = OneMax
    else:
        problem = LeadingOne

    if args.alg == 'rls_lo':
        problem = LeadingOne

    sparams = alg_dict[args.alg]['params']
    alg_func = alg_dict[args.alg]['func']
    if sparams:
        ls = sparams.split(",")
        params = {}
        for s in ls:
            name = s.strip().split('=')[0]
            val = s.strip().split('=')[1]
            if ('lbd' in name) or ('k' in name):
                val = int(val)
            else:
                val = float(val)
            params[name] = val
        x, f_x, ne = alg_func(args.n, seed=args.seed, problem=problem, **params)
    else:
        sparams=""
        x, f_x, ne = alg_func(args.n, seed=args.seed, problem=problem)    
    
    print("n,seed,optimal,n_evals,f,alg")
    print("%d,%d,%d,%d,%d,%s" % (args.n,args.seed,int(x.is_optimal()), ne, f_x, args.alg))

main()


