from irace_launcher import IraceCallerBinningWithDefaults
import argparse
from config import load_or_run_binning_comparison_validation, trials, threads, iterative_seeding_iterations, iterative_seeding_sizes, iterative_seeding_multiples, get_iter_bins, iterative_seeding_seeds
import json
from irace_grapher import next_randoms
import numpy
from multiprocessing import Pool
import sys
import json

def main(i, j, tuner_seeds, grapher_seeds):
  size = iterative_seeding_sizes[i]
  if j == 0:
    previous_lbds = None
  else:
    with open(f'irace_output/best_lbds_binning_with_defaults_{size}_{iterative_seeding_multiples[i][j-1]}_{j-1}_{tuner_seeds[j-1]}_{grapher_seeds[j-1]}.json') as f:
      previous_lbds = json.load(f)
  pool = Pool(threads)
  tuner_seed = tuner_seeds[j]
  grapher_seed = grapher_seeds[j]
  caller = IraceCallerBinningWithDefaults(size, j, iterative_seeding_multiples[i][j], previous_lbds, get_iter_bins(size, j+1), tuner_seed)
  caller.run()
  with open(f"irace_output/binning_with_defaults_{size}_{iterative_seeding_multiples[i][j]}_{j}_{tuner_seed}.json", "w") as f:
    json.dump(caller.best_config, f)
  rng = numpy.random.default_rng(grapher_seed)
  previous_lbds = caller.best_config
  with open(f'irace_output/best_lbds_binning_with_defaults_{size}_{iterative_seeding_multiples[i][j]}_{j}_{tuner_seed}_{grapher_seed}.json', 'w') as f:
    json.dump(previous_lbds, f)
  load_or_run_binning_comparison_validation(size, f'irace_output/performance_binning_with_defaults_{size}_{iterative_seeding_multiples[i][j]}_{j}_{tuner_seed}_{grapher_seed}.json', caller.best_config, next_randoms(rng, trials), pool, logging=True)


if __name__ == '__main__':
  io = int(sys.argv[1])
  jo = int(sys.argv[2])
  iteration_count = iterative_seeding_iterations[io]
  tuner_seeds = iterative_seeding_seeds[io][0]
  grapher_seeds = iterative_seeding_seeds[io][1]
  main(io, jo, tuner_seeds, grapher_seeds)
  