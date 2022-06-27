import multiprocessing
import os
from dotenv import load_dotenv
from onell_algs import onell_lambda, onell_dynamic_5params, onell_dynamic_theory
import json
from matplotlib import pyplot as plt

load_dotenv()

SMALL = os.getenv("SMALL", None)
EMAIL = os.getenv("EMAIL", "false").strip() == "true"

if SMALL == "small":
  N = 3
elif SMALL == "xsmall":
  N = 2
else:
  N = 6

trials = 500 
threads = int(multiprocessing.cpu_count() * 1.5)
smac_instances = 36
seed = 16950281577708742744
seed_small = 2213319694
descend_rate = 1.5
first_bin_portion = 1-(1/descend_rate)

sizes = [
  10, 
  50, 
  100,
  200, 
  500,
  1000
]

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
  ] 

if SMALL=="small":
  experiment_multiples_static = [50, 30, 20, 10, 10, 10]
elif SMALL=="xsmall":
  experiment_multiples_static = [1, 1]
else: 
  experiment_multiples_static = [100] * N

def get_bins(size):
  bins = []
  bin_lookup = []
  remaining = size
  bin_size = int(size * first_bin_portion)
  i = 0
  while remaining:
    bins.append(bin_size)
    remaining -= bin_size
    for _ in range(bin_size):
      bin_lookup.append(i)
    bin_size = int(bin_size / descend_rate)
    if bin_size < 1:
      bin_size = 1
    i += 1
  return bins, bin_lookup

def onell_lambda_positional(size, lbds, seed):
  _, _, performance = onell_lambda(size, lbds=lbds, seed=seed)
  return performance

def onell_dynamic_5params_positional(size, seed): 
  _, _, performance = onell_dynamic_5params(size, seed=seed)
  return performance

def onell_dynamic_theory_positional(size, seed):
  _, _, performance = onell_dynamic_theory(size, seed=seed)
  return performance

def graph(json_path, png_path, dynamic_lbd_performance, dynamic_lbd_bin_performance, static_lbd_performance, random_dynamic_lbd_performance, random_static_lbd_performance, one_lbd_performance, dynamic_theory_performance, dynamic_5params_performance):
  data = (dynamic_lbd_performance, dynamic_lbd_bin_performance, static_lbd_performance, random_dynamic_lbd_performance, random_static_lbd_performance, one_lbd_performance, dynamic_theory_performance, dynamic_5params_performance)
  with open(json_path, 'w') as f:
    json.dump(data, f)
  figure, ax = plt.subplots(figsize=(12,5))
  figure.subplots_adjust(left=0.25)
  ax.boxplot(data, labels=("Dynamic Lambda", "Dynamic Lambda with binning", "Static Lambda", "Random Dynamic Lambda", "Random Static Lambda", "Lambda = 1", "Dynamic Theory", "Five Parameters"), vert=False)
  figure.savefig(png_path, dpi=300)
