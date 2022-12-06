from onell_algs_rs import onell_lambda
from config import binning_with_dp_iterations, binning_with_dp_sizes, binning_with_dp_seeds, get_iter_bins, get_dp_lbd, BinningWithPolicyStrategy, load_or_run_binning_comparison_validation, flatten_lbds, trials, threads
from irace_grapher import next_randoms
from multiprocessing import Pool
import numpy as np
import argparse

mv = {
    BinningWithPolicyStrategy.start: 'binning_with_dp_start',
    BinningWithPolicyStrategy.end: 'binning_with_dp_end', 
    BinningWithPolicyStrategy.middle: 'binning_with_dp_middle', 
}

def main(i, grapher_seed):
    size = binning_with_dp_sizes[i]
    bin_count = binning_with_dp_iterations[i]
    bins = get_iter_bins(size, bin_count)
    pool = Pool(threads)
    rng = np.random.default_rng(grapher_seed)
    for strategy in [BinningWithPolicyStrategy.start, BinningWithPolicyStrategy.end, BinningWithPolicyStrategy.middle]:
        lbd = get_dp_lbd(size, bin_count, strategy)
        load_or_run_binning_comparison_validation(size, f"irace_output/performance_{mv[strategy]}_{i}_{grapher_seed}.json", flatten_lbds(lbd, bins), next_randoms(rng, trials), pool)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('i', type=int)
    args = parser.parse_args()
    main(args.i, binning_with_dp_seeds[args.i])
