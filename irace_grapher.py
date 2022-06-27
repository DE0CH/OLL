import argparse
import json
from config import sizes, experiment_multiples_dynamic, experiment_multiples_static, threads, trials, onell_lambda_positional, onell_dynamic_theory_positional, onell_dynamic_5params_positional, graph
import numpy
from multiprocessing import Pool

def next_randoms(rng: numpy.random.Generator, size):
  return rng.integers(1<<15, (1<<16)-1, size)

def main(i, dynamic_seed, dynamic_bin_seed, static_seed, seed):
  pool = Pool(threads)
  rng = numpy.random.default_rng(seed)
  with open(f"irace_output/best_config_dynamic_{sizes[i]}_{experiment_multiples_dynamic[i]}_{dynamic_seed}.json") as f:
    dynamic_best_config = json.load(f)
  with open(f"irace_output/best_config_dynamic_bin_{sizes[i]}_{experiment_multiples_dynamic[i]}_{dynamic_bin_seed}.json") as f:
    dynamic_bin_best_config = json.load(f)
  with open(f"irace_output/best_config_static_{sizes[i]}_{experiment_multiples_static[i]}_{static_seed}.json") as f:
    static_best_config = json.load(f)
  dynamic_performance = pool.starmap(onell_lambda_positional, zip([sizes[i]]*trials, [dynamic_best_config] * trials, next_randoms(rng, trials)))
  dynamic_bin_performance = pool.starmap(onell_lambda_positional, zip([sizes[i]]*trials, [dynamic_bin_best_config] * trials, next_randoms(rng, trials)))
  static_performance = pool.starmap(onell_lambda_positional, zip([sizes[i]]*trials, [static_best_config] * trials, next_randoms(rng, trials)))
  random_dynamic_performance = pool.starmap(onell_lambda_positional, zip([sizes[i]]*trials, [list(rng.integers(1, sizes[i], sizes[i])) for _ in range(trials)], next_randoms(rng, trials)))
  random_static_performance = pool.starmap(onell_lambda_positional, zip([sizes[i]]*trials, [[rng.integers(1, sizes[i])] * sizes[i] for _ in range(trials)], next_randoms(rng, trials)))
  one_performance = pool.starmap(onell_lambda_positional, zip([sizes[i]]*trials, [[1] * sizes[i]]*trials, next_randoms(rng, trials)))
  dynamic_theory_performance = pool.starmap(onell_dynamic_theory_positional, zip([sizes[i]]*trials, next_randoms(rng, trials)))
  five_parameters_performance = pool.starmap(onell_dynamic_5params_positional, zip([sizes[i]]*trials, next_randoms(rng, trials)))

  # TODO, save result and put them in a graph
  graph(
    f"irace_output/performance_{sizes[i]}_{experiment_multiples_dynamic[i]}_{experiment_multiples_static[i]}.json",
    f"irace_output/performance_{sizes[i]}_{experiment_multiples_dynamic[i]}_{experiment_multiples_static[i]}.png",
    dynamic_performance,
    dynamic_bin_performance,
    static_performance,
    random_dynamic_performance,
    random_static_performance,
    one_performance,
    dynamic_theory_performance,
    five_parameters_performance 
  )


  
# Dynamic lbd, dynamic lbd with binning, static lambda, random dynamic lambda, random static lambda, lambda = 1, dynmaic_theory, 5 parameters


if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('i', type=int)
  parser.add_argument('dynamic_seed', type=int)
  parser.add_argument('dynamic_bin_seed', type=int)
  parser.add_argument('static_seed', type=int)
  parser.add_argument('seed', type=int)
  args = parser.parse_args()
  main(args.i, args.dynamic_seed, args.dynamic_bin_seed, args.static_seed, args.seed)