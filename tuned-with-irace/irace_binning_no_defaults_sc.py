from irace_launcher import IraceCallerBinningNoDefaults
import argparse
from config import load_or_run_binning_comparison_validation, trials, threads, get_iter_bins, binning_no_defaults_sc_n, binning_no_defaults_sc_iteration, binning_no_defaults_sc_multiples, binning_no_defaults_sc_seeds
import json
from irace_grapher import next_randoms
import numpy
from multiprocessing import Pool
import sys

def main(size, j, multiple, tuner_seed, grapher_seed):
  pool = Pool(threads)
  caller = IraceCallerBinningNoDefaults(size, j, multiple, None ,get_iter_bins(size, j+1), tuner_seed, type_name='binning_no_defaults_sc')
  caller.run()
  with open(f"irace_output/binning_no_defaults_sc_{size}_{multiple}_{j}_{tuner_seed}.json", "w") as f:
    json.dump(caller.best_config, f)
  rng = numpy.random.default_rng(grapher_seed)
  load_or_run_binning_comparison_validation(size, f'irace_output/performance_binning_no_defaults_sc_{size}_{multiple}_{j}_{tuner_seed}_{grapher_seed}.json', caller.best_config, next_randoms(rng, trials), pool, logging=True)


if __name__ == '__main__':
  io = int(sys.argv[1])
  size = binning_no_defaults_sc_n[io]
  j = binning_no_defaults_sc_iteration[io]
  multiple = binning_no_defaults_sc_multiples[io]
  tuner_seed = binning_no_defaults_sc_seeds[0][io]
  grapher_seed = binning_no_defaults_sc_seeds[1][io]
  main(size, j, multiple, tuner_seed, grapher_seed)
  