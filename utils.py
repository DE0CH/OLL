from onell_algs import onell_lambda, onell_dynamic_theory, onell_dynamic_5params
import numpy
from config import trials
import os
import json
import matplotlib.pyplot as plt

def onell_eval(f, n, lbds, seed):
  if lbds:
    res = f(n, lbds=lbds, seed=seed)
  else:
    res = f(n, seed=seed)
  if res[1] != n:
    print(f"Capped with {f}, {n}, {lbds}, {seed}")
  return res[2]

def graph(n, output_dir, static_multiple, dynamic_multiple, static_lbd, dynamic_lbd, rng, pool):
  def next_seeds(size):
    res = list(rng.integers(low=10**10, high=10**11, size=size))
    return res  
  json_path = os.path.join(output_dir, f"performace_{n}_{static_multiple}_{dynamic_multiple}.json")
  png_path = os.path.join(output_dir, f"box_plot_{n}_{static_multiple}_{dynamic_multiple}.png")
  if not os.path.isfile(json_path):
    random_lbd_set = [list(rng.integers(low=1, high=n, size=n)) for _ in range(trials)]
    random_lbd = list(rng.integers(low=1, high=n, size=n))
    static_lbd_performace = pool.starmap(onell_eval, zip([onell_lambda]*trials, [n]*trials, [static_lbd]*trials, next_seeds(trials)))
    dynamic_lbd_performace = pool.starmap(onell_eval, zip([onell_lambda]*trials, [n]*trials, [dynamic_lbd]*trials, next_seeds(trials)))
    random_lbd_performace = pool.starmap(onell_eval, zip([onell_lambda]*trials, [n]*trials, random_lbd_set, next_seeds(trials)))
    random_lbd_same_performace = pool.starmap(onell_eval, zip([onell_lambda]*trials, [n]*trials, [random_lbd]*trials, next_seeds(trials)))
    one_lbd_performace = pool.starmap(onell_eval, zip([onell_lambda]*trials, [n]*trials, [[1]*n]*trials, next_seeds(trials)))
    dynamic_theory_performace = pool.starmap(onell_eval, zip([onell_dynamic_theory]*trials, [n]*trials, [None]*trials, next_seeds(trials)))
    five_param_performace = pool.starmap(onell_eval, zip([onell_dynamic_5params]*trials, [n]*trials, [None]*trials, next_seeds(trials)))
    with open(json_path, "w") as f:
      json.dump((static_lbd_performace, dynamic_lbd_performace, random_lbd_performace, random_lbd_same_performace, one_lbd_performace, dynamic_theory_performace, five_param_performace), f)
  else:
    with open(json_path) as f:
      static_lbd_performace, dynamic_lbd_performace, random_lbd_performace, random_lbd_same_performace, one_lbd_performace, dynamic_theory_performace, five_param_performace = json.load(f)
  figure, ax = plt.subplots(figsize=(12,5))
  figure.subplots_adjust(left=0.25)
  ax.boxplot((static_lbd_performace, dynamic_lbd_performace, random_lbd_performace, random_lbd_same_performace, one_lbd_performace, dynamic_theory_performace, five_param_performace), labels=(f"Static Lambda (lbd={5})", "Dynamic Lambda", "Random Lambda (Lambda changes)", "Random Lambda (Lambda fixed)", "Lambda = 1", "Dynamic Theory", "Five Parameters"), vert=False)
  figure.savefig(png_path, dpi=300)
  