from onell_algs_rs import onell_lambda
from config import optimal_dynamic_sizes, optimal_dynamic_lbds, optimal_dynamic_seeds, load_or_run_binning_comparison_validation, trials, threads
from irace_grapher import next_randoms
from multiprocessing import Pool
import numpy as np
import argparse

def main(i, grapher_seed):
    size = optimal_dynamic_sizes[i]
    pool = Pool(threads)
    rng = np.random.default_rng(grapher_seed)
    lbds = optimal_dynamic_lbds[i]
    load_or_run_binning_comparison_validation(size, f"irace_output/performance_optimal_dynamic_{i}_{grapher_seed}.json", lbds, next_randoms(rng, trials), pool)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('i', type=int)
    args = parser.parse_args()
    main(args.i, optimal_dynamic_seeds[args.i])
