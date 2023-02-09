from irace_launcher import IraceCallerDynamicWithStatic
import argparse
from config import sizes, experiment_multiples_dynamic, load_or_run_binning_comparison_validation, trials, threads
import json
from irace_grapher import next_randoms
import numpy
from multiprocessing import Pool

def main(i, tuner_seed, grapher_seed):
  caller = IraceCallerDynamicWithStatic(sizes[i], experiment_multiples_dynamic[i], tuner_seed)
  caller.run()
  with open(f"irace_output/best_config_dynamic_with_static_{sizes[i]}_{experiment_multiples_dynamic[i]}_{tuner_seed}.json", "w") as f:
    json.dump(caller.best_config, f)
  pool = Pool(threads)
  rng = numpy.random.default_rng(grapher_seed)
  load_or_run_binning_comparison_validation(sizes[i], f'irace_output/performance_dynamic_with_static_{sizes[i]}_{experiment_multiples_dynamic[i]}_{tuner_seed}_{grapher_seed}.json', caller.best_config, next_randoms(rng, trials), pool)

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('i', type=int)
  parser.add_argument('tuner_seed', type=int)
  parser.add_argument('grapher_seed', type=int)
  args = parser.parse_args()
  main(args.i, args.tuner_seed, args.grapher_seed)
  