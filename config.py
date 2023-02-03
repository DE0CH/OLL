import multiprocessing
import os
try:
  from onell_algs_rs import onell_dynamic_theory, onell_lambda, onell_five_parameters, onell_lambda_with_log
except:
  pass
import json
from enum import Enum 
from math import sqrt


SMALL = os.getenv("SMALL", None)
EMAIL = os.getenv("EMAIL", "false").strip() == "true"

if SMALL == "small":
  N = 3
  N_lock = 3
elif SMALL == "xsmall":
  N = 2
  N_lock = 2
else:
  N = 9
  N_lock = 8

# N_lock used because some seeds will shuffle if N is changed.

if SMALL == "small" or SMALL == 'xsmall':
  M = 3
else:
  M = 13

# be careful when changing M because changing M will cause seeds to shuffle

if SMALL == 'small':
  trials = 3
else:
  trials = 500 
threads = int(multiprocessing.cpu_count() * 1.25)
smac_instances = 36
seed = 16950281577708742744
seed_small = 2213319694
descent_rate = 2

descent_rates = ([1.5 + (i*(1/(11-1))) for i in range(11)] + [5, 8])[:M]

sizes = [
  10, 
  50, 
  100,
  200, 
  500,
  1000,
  2000,
  5000,
  3000,
]

N_baseline_seeds = [
  [63695],
  [59703],
  [57290],
  [40239],
] # Previous, I generated seeds in irace_load_distributor and soon realized it was a bad idea because it makes adding new configuration without messing up the seeds extremely difficult, but I don't want to touch old code because I can mess it up, so I just retrofit this way of defining seeds after n = 5000

N_binning_seeds_new = [
  [[58127, 60157, 60010, 49694, 64369, 55020, 37922, 40125, 35448, 43996, 49943, 58824, 40591]],
  [[34890, 51902, 62805, 39459, 64714, 41456, 42789, 61557, 54121, 56972, 48582, 37467, 58445]],
]

N_binning_with_static_new = [
  [[56049, 37079, 44282, 59018, 45498, 37209, 43477, 52292, 60889, 47679, 46931, 60369, 63193]],
  [[55087, 65029, 56297, 63675, 41421, 33054, 64102, 60375, 58352, 39134, 45547, 61359, 64024]],
]

N_dynamic_with_static_seeds = [
  [33014],
  [35312],
]


sizes_reverse = {}
for i, size in enumerate(sizes):
  sizes_reverse[size] = i

if SMALL == "small":
  experiment_multiples_dynamic = [
    50, 
    30, 
    20, 
    10,
    10,
    10
  ]
elif SMALL == "xsmall":
  experiment_multiples_dynamic = [
    10, 
    10,
  ]
else:
  experiment_multiples_dynamic = [
    5*10**3, 
    10**3,
    5*10**2,
    250,
    100,
    50,
    25,
    10,
    10
  ] 

default_lbds = [
  1.0077,
  1.0734, 
  6.5656,
  4.8881,
  6.9282,
  6.7279,
  8.0286,
  8.7281,
  8.7417,
]

if SMALL=="small":
  experiment_multiples_static = [50, 30, 20, 10, 10, 10]
elif SMALL=="xsmall":
  experiment_multiples_static = [1, 1]
else: 
  experiment_multiples_static = [100, 100, 100, 100, 100, 100, 100, 10, 10]

experiment_multiples_dynamic_bin = experiment_multiples_dynamic

def get_bins(size, descent_rate=descent_rate):
  bins = []
  bin_lookup = []
  remaining = size
  first_bin_portion = 1-(1/descent_rate)
  bin_size = int(size * first_bin_portion)
  if bin_size < 1 :
    bin_size = 1
  i = 0
  while remaining:
    bins.append(bin_size)
    remaining -= bin_size
    for _ in range(bin_size):
      bin_lookup.append(i)
    bin_size = int(bin_size / descent_rate)
    if bin_size < 1:
      bin_size = 1
    i += 1
  return bins, bin_lookup

def onell_lambda_positional(size, lbds, seed):
  performance = onell_lambda(size, lbds, seed, get_cutoff(size))
  return performance

def onell_dynamic_5params_positional(size, seed): 
  performance = onell_five_parameters(size, seed, get_cutoff(size))
  return performance

def onell_dynamic_theory_positional(size, seed):
  performance = onell_dynamic_theory(size, seed, get_cutoff(size))
  return performance

def graph(json_path, png_path, dynamic_lbd_performance, dynamic_lbd_bin_performance, static_lbd_performance, one_lbd_performance, dynamic_theory_performance, dynamic_5params_performance):
  from matplotlib import pyplot as plt
  data = (dynamic_lbd_performance, dynamic_lbd_bin_performance, static_lbd_performance, one_lbd_performance, dynamic_theory_performance, dynamic_5params_performance)
  with open(json_path, 'w') as f:
    json.dump(data, f)
  figure, ax = plt.subplots(figsize=(12,5))
  figure.subplots_adjust(left=0.25)
  ax.boxplot(data, labels=("Dynamic Lambda", "Dynamic Lambda with binning", "Static Lambda", "Lambda = 1", "Dynamic Theory", "Five Parameters"), vert=False)
  figure.savefig(png_path, dpi=300)

def get_cutoff(size):
  if size == 5000 or size == 4000 or size == 3000:
    return 250000
  return 99999999

from contextlib import contextmanager,redirect_stderr,redirect_stdout
from os import devnull

@contextmanager
def suppress_stderr():
    """A context manager that redirects stdout and stderr to devnull"""
    with open(devnull, 'w') as fnull:
        with redirect_stderr(fnull) as err:
            yield (err, )
  

experiment_types = ['dynamic_theory', 'dynamic', 'static', 'binning_comparison', 'binning_comparison_with_static', 'dynamic_with_static', 'binning_with_defaults', 'binning_with_dynamic_start', 'binning_with_dynamic_end', 'binning_with_dynamic_middle', 'binning_no_defaults', 'binning_with_dp_start', 'binning_with_dp_end', 'binning_with_dp_middle', 'binning_no_defaults_sc', 'binning_with_defaults_sc']

def load_or_run_binning_comparison_validation(size, file_name, best_config, seeds, pool, logging=False):
    if not logging:
      try:
        with open(file_name) as f:
          performances = json.load(f)
      except:
        performances = pool.starmap(onell_lambda_positional, zip([size]*trials, [best_config] * trials, seeds))
        with open(file_name, "w") as f:
          json.dump(performances, f)
    else:
      try:
        with open(f"{file_name}.log.json") as f:
          json.load(f)
        with open(file_name) as f:
          json.load(f)
      except:
        results = pool.starmap(onell_lambda_with_log, zip([size]*trials, [best_config] * trials, seeds, [get_cutoff(size)] * trials))
        performances = []
        fxss = []
        n_evalsss = []
        for a, b, c in results:
          performances.append(a)
          fxss.append(b)
          n_evalsss.append(c)
        with open(file_name, "w") as f:
          json.dump(performances, f)
        with open(f"{file_name}.log.json", "w") as f:
          json.dump((fxss, n_evalsss), f)

min_cpu_usage = 0.75
max_cpu_usage = 0.95

if SMALL == 'small':
  N2 = 2
else:
  N2 = 4

if SMALL == 'small':
  iterative_seeding_sizes = [20, 40]
  iterative_seeding_multiples = [[50] * 5, [50] * 6]
  iterative_seeding_iterations = [5, 6]
elif SMALL == 'xsmall':
  raise NotImplementedError('xsmall is no longer supported')
else:
  iterative_seeding_sizes = [2000, 3000, 500, 1000]
  iterative_seeding_multiples = [[10] * 11, [7] * 12, [10] * 9, [10] * 10]
  iterative_seeding_iterations = [11, 12, 9, 10]
iterative_seeding_seeds = [
  [[45937, 35062, 62556, 33221, 62291, 56368, 64176, 53501, 38816, 48628, 56170], [41639, 48005, 47960, 44150, 36705, 55294, 63274, 64432, 35089, 41214, 34467]],
  [[64752, 44788, 48831, 44689, 57412, 55395, 57062, 47129, 59139, 64221, 53506, 37951], [40895, 55427, 42053, 42228, 44567, 64559, 53729, 44427, 33403, 34618, 56112, 51163]],
  [[61399, 60059, 49072, 45454, 61011, 51557, 37357, 38997, 62510], [51865, 50622, 57932, 51864, 61672, 33226, 41980, 37757, 57918]],
  [[65329, 63900, 62488, 59570, 64864, 35518, 52107, 62970, 38398, 55654], [47929, 65221, 45302, 54322, 53979, 39677, 45773, 44390, 43380, 59791]],
] # tuner_seed, grapher_seed

if SMALL == 'small':
  binning_with_dynamic_sizes = [20, 40]
  binning_with_dynamic_iterations = [5, 6]
else:
  binning_with_dynamic_sizes = [2000, 3000, 500, 1000]
  binning_with_dynamic_iterations = [11, 12, 9, 10]

binning_with_dynamic_seeds = [50043, 39994, 50380, 64481]

N3 = 2
binning_with_dp_sizes = [500, 1000]
binning_with_dp_iterations = [9, 10]
binning_with_dp_seeds = [37856, 58646]

dp_policies = {
  500: [500, 499, 499, 499, 499, 499, 499, 499, 499, 499, 499, 499, 499, 499, 499, 499, 498, 498, 498, 498, 498, 498, 498, 498, 498, 498, 498, 498, 498, 498, 498, 498, 498, 498, 497, 497, 497, 497, 497, 497, 497, 497, 497, 497, 497, 497, 497, 497, 497, 496, 496, 496, 496, 496, 496, 496, 496, 496, 496, 496, 496, 496, 495, 495, 495, 495, 495, 495, 495, 495, 495, 495, 494, 494, 494, 494, 494, 494, 494, 493, 493, 493, 493, 493, 493, 492, 492, 492, 492, 491, 491, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 6, 6, 6, 6, 6, 6, 6, 6, 6, 7, 7, 7, 7, 7, 7, 7, 8, 8, 8, 8, 9, 9, 9, 10, 10, 11, 11, 12, 14, 15, 18, 25],
  1000: [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 8, 8, 8, 8, 8, 8, 8, 8, 8, 9, 9, 9, 9, 9, 9, 10, 10, 10, 10, 11, 11, 11, 12, 12, 13, 13, 14, 15, 16, 17, 19, 21, 26, 36]
}

N4 = 10
if SMALL == 'small':
  binning_no_defaults_sc_n = [20] * 5 + [40] * 5
  binning_no_defaults_sc_iteration = [4] * 5 + [5] * 5
  binning_no_defaults_sc_multiples = [50] * 5 + [50] * 5
else:
  binning_no_defaults_sc_n = [500] * 5 + [1000] * 5
  binning_no_defaults_sc_iteration = [5] * 5 + [6] * 5
  binning_no_defaults_sc_multiples = [10] * 5 + [10] * 5

binning_no_defaults_sc_seeds = [
  [39950, 59058, 42580, 36276, 44129, 42038, 59214, 47012, 64959, 33763],
  [65037, 50144, 47378, 41249, 41628, 63956, 54818, 40896, 59625, 39378]
]

N5 = N4
binning_with_defaults_sc_n = binning_no_defaults_sc_n
binning_with_defaults_sc_iteration = binning_no_defaults_sc_iteration
binning_with_defaults_sc_multiples = binning_no_defaults_sc_multiples
binning_with_defaults_sc_seeds = [
  [63695, 59703, 57290, 40239, 58127, 60157, 60010, 49694, 64369, 55020],
  [37922, 40125, 35448, 43996, 49943, 58824, 40591, 34890, 51902, 62805]
]
binning_with_defaults_sc_iterative_size_reverse = [iterative_seeding_sizes.index(binning_no_defaults_sc_n[i]) for i in range(N5)] # This is currently a O(N^2) operation, but since N is so small it doesn't matter
binning_with_defaults_sc_flag_depends_on = [(binning_with_defaults_sc_iterative_size_reverse[i], binning_with_defaults_sc_iteration[i]) for i in range(N5)]

def get_iter_bins(size, bin_count):
  res = [0]
  for j in range(bin_count-1):
    res.append(size - size // 2**(j+1))
  res.append(size)
  return res

def flatten_lbds(lbds, bins):
  # bin is cumulative
  res = []
  i = 0
  j = 0
  while j < bins[-1]:
    res.append(lbds[i])
    j += 1
    if j == bins[i+1]:
      i += 1
  return res

class BinningWithPolicyStrategy(Enum):
  start = 'start'
  end = 'end'
  middle = 'middle'

def get_dynamic_theory_lbd(size, bin_count, strategy: BinningWithPolicyStrategy):
  return get_binning_policy_lbd(size, bin_count, strategy, lambda x: sqrt(size / (size - x)))

def get_dp_lbd(size, bin_count, strategy: BinningWithPolicyStrategy):
  if size not in binning_with_dp_sizes:
    raise NotImplementedError(f"No data for the required size {size}")
  return get_binning_policy_lbd(size, bin_count, strategy, lambda x: dp_policies[size][x])

def get_binning_policy_lbd(size, bin_count, strategy: BinningWithPolicyStrategy, f):
  bins = get_iter_bins(size, bin_count)
  lbds = []
  if strategy == BinningWithPolicyStrategy.start:
    for i in range(bin_count):
      lbds.append(f(bins[i]))
  elif strategy == BinningWithPolicyStrategy.end:
    for i in range(bin_count):
      lbds.append(f(bins[i+1]-1))
  elif strategy == BinningWithPolicyStrategy.middle:
    for i in range(bin_count):
      lbds.append(f((bins[i] + bins[i+1]) // 2))
  else:
    raise NotImplementedError("The current BinningWithDynamicStrategy is not implemented")
  return lbds  

def c_string(c, size, bound):
  if c == 2**64-1:
    if bound == get_cutoff(size):
      return 'Inf'
    else:
      return str(bound + 1)
  else:
    return str(c)

def d_string(c, size, bound):
  if c == 2**64-1:
    if bound == get_cutoff(size):
      return '0'
    else:
      return str(bound + 1)
  else:
    return str(c)
