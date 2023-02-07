from onell_algs_rs import onell_lambda
from config import optimal_dynamic_binned_sizes, optimal_dynamic_binned_lbds, optimal_dynamic_binned_seeds, get_iter_bins, load_or_run_binning_comparison_validation, flatten_lbds, trials, threads
from irace_grapher import next_randoms
from multiprocessing import Pool
import numpy as np
import argparse

def main(i, grapher_seed):
    size = optimal_dynamic_binned_sizes[i]
    bin_count = len(optimal_dynamic_binned_lbds[i])
    bins = get_iter_bins(size, bin_count)
    pool = Pool(threads)
    rng = np.random.default_rng(grapher_seed)
    lbd = optimal_dynamic_binned_lbds[i]
    load_or_run_binning_comparison_validation(size, f"irace_output/performance_optimal_dynamic_binned_{i}_{grapher_seed}.json", flatten_lbds(lbd, bins), next_randoms(rng, trials), pool)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('i', type=int)
    args = parser.parse_args()
    main(args.i, optimal_dynamic_binned_seeds[args.i])
