from onell_algs_rs import onell_lambda
from config import binning_with_dynamic_iterations, binning_with_dynamic_sizes, binning_with_dynamic_seeds, get_iter_bins, get_dynamic_theory_lbd, BinningWithDynamicStrategy, load_or_run_binning_comparison_validation, flatten_lbds, trials, threads
from irace_grapher import next_randoms
from multiprocessing import Pool
import numpy as np
import argparse

mv = {
    BinningWithDynamicStrategy.start: 'binning_with_dynamic_start',
    BinningWithDynamicStrategy.end: 'binning_with_dynamic_end', 
    BinningWithDynamicStrategy.middle: 'binning_with_dynamic_middle', 
}

def main(i, grapher_seed):
    size = binning_with_dynamic_sizes[i]
    bin_count = binning_with_dynamic_iterations[i]
    bins = get_iter_bins(size, bin_count)
    pool = Pool(threads)
    rng = np.random.default_rng(grapher_seed)
    for strategy in [BinningWithDynamicStrategy.start, BinningWithDynamicStrategy.end, BinningWithDynamicStrategy.middle]:
        lbd = get_dynamic_theory_lbd(size, bin_count, strategy)
        load_or_run_binning_comparison_validation(size, f"irace_output/performance_{mv[strategy]}_{i}_{grapher_seed}.json", flatten_lbds(lbd, bins), next_randoms(rng, trials), pool)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('i', type=int)
    args = parser.parse_args()
    main(args.i, binning_with_dynamic_seeds[args.i])
