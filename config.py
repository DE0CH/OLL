import multiprocessing
import os
try:
  from onell_algs_rs import onell_dynamic_theory, onell_lambda, onell_five_parameters
except:
  pass
import json



SMALL = os.getenv("SMALL", None)
EMAIL = os.getenv("EMAIL", "false").strip() == "true"

if SMALL == "small":
  N = 3
elif SMALL == "xsmall":
  N = 2
else:
  N = 8

if SMALL == "small" or SMALL == 'xsmall':
  M = 3
else:
  M = 13

trials = 500 
threads = int(multiprocessing.cpu_count() * 0.75)
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
  ] 

default_lbds = [
  1.0077,
  1.0734, 
  6.5656,
  4.8881,
  6.9282,
  6.7279,
  8.0286,
  8.7281
]

if SMALL=="small":
  experiment_multiples_static = [50, 30, 20, 10, 10, 10]
elif SMALL=="xsmall":
  experiment_multiples_static = [1, 1]
else: 
  experiment_multiples_static = [100] * (N-1) + [experiment_multiples_dynamic[-1]]

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
  if size == 5000:
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
  

experiment_types = ['dynamic_theory', 'dynamic', 'static', 'binning_comparison', 'binning_comparison_with_static', 'dynamic_with_static']

def load_or_run_binning_comparison_validation(size, file_name, best_config, seeds, pool):
  try:
    with open(file_name) as f:
      performances = json.load(f)
  except:
    performances = pool.starmap(onell_lambda_positional, zip([size]*trials, [best_config] * trials, seeds))
    with open(file_name, "w") as f:
      json.dump(performances, f)

min_cpu_usage = 0.75
max_cpu_usage = 0.95

