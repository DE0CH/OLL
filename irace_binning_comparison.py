from irace_launcher import IraceCallerBinningComparison
import argparse
from config import sizes, experiment_multiples_dynamic_bin, descent_rates, threads, trials, onell_lambda_positional
from irace_grapher import next_randoms
import json
from multiprocessing import Pool
import numpy

def main(i, j, tuner_seed, grapher_seed):
  caller = IraceCallerBinningComparison(sizes[i], experiment_multiples_dynamic_bin[i], j, tuner_seed)
  caller.run()
  with open(f"irace_output/best_config_binning_comparison_{sizes[i]}_{experiment_multiples_dynamic_bin[i]}_{descent_rates[j]}_{tuner_seed}.json", "w") as f:
    json.dump(caller.best_config, f)
  pool = Pool(threads)
  rng = numpy.random.default_rng(tuner_seed)
  performances = pool.starmap(onell_lambda_positional, zip([sizes[i]]*trials, [caller.best_config] * trials, next_randoms(rng, trials)))
  with open(f"irace_output/performance_binning_comparison_{sizes[i]}_{experiment_multiples_dynamic_bin[i]}_{descent_rates[j]}_{tuner_seed}_{grapher_seed}.json", "w") as f:
    json.dump(performances, f)


if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('i', type=int)
  parser.add_argument('j', type=int)
  parser.add_argument('tuner_seed', type=int)
  parser.add_argument('grapher_seed', type=int)
  args = parser.parse_args()
  main(args.i, args.j, args.tuner_seed, args.grapher_seed)