import logging
from threading import Thread

logging.basicConfig(level=logging.INFO)

import numpy as np
import os
from multiprocessing.pool import Pool, ThreadPool

from ConfigSpace.hyperparameters import UniformFloatHyperparameter, UniformIntegerHyperparameter

# Import ConfigSpace and different types of parameters
from smac.configspace import ConfigurationSpace
from smac.facade.smac_bb_facade import SMAC4BB
from smac.facade.smac_ac_facade import SMAC4AC

# Import SMAC-utilities
from smac.scenario.scenario import Scenario
from onell_algs import onell_dynamic_5params, onell_lambda, onell_dynamic_theory


from config import seed_small as seed, N, sizes, experiment_multiples_dynamic, experiment_multiples_static, threads, EMAIL, trials, smac_instances, first_bin_portion, descent_rate
import json
import argparse
from dataclasses import dataclass
import matplotlib.pyplot as plt
from pathlib import Path

@dataclass
class OnellType:
  dynamic = 1
  static = 2
  dynamic_bin = 3

class SmacCaller:
  def __init__(self, type_name, size, experiment_multiple, seed, output_dir="smac_output"):
    self.output_dir = output_dir
    self.size = size
    self.experiment_multiple = experiment_multiple
    self.seed = seed
    self.type_name = type_name
    self.cs = ConfigurationSpace()
    self.best_config_dict = None
    self.runner = None
    self.best_config_file_path = os.path.join(self.output_dir, f"best_config_{self.type_name}_{self.size}_{self.experiment_multiple}_{self.seed}.json")


  def config(self):
    self.scenario = Scenario({
      "run_obj": "quality",  # we optimize quality (alternatively runtime)
      "ta_run_limit": round(self.size*self.experiment_multiple),  # max. number of function calls
      "cs": self.cs,  # configuration space
      "deterministic": "false",
      "output_dir": os.path.join(self.output_dir, f"{self.type_name}_{self.size}_{self.experiment_multiple}"), 
      "wallclock_limit": 338400
    })
    self.smac = SMAC4AC(
      scenario=self.scenario,
      rng=np.random.RandomState(self.seed),
      tae_runner=self.runner,
    )

  def parse_result(self):
    '''Parse the result from the raw dictionary into self.best_config, which is a list of lambdas'''
    raise NotImplementedError()

  def run(self):
    try:
      with open(self.best_config_file_path) as f:
        self.best_config = json.load(f)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
      self.config()
      logging.info("Finished Config")
      self.best_config_dict = self.smac.optimize().get_dictionary()
      self.parse_result()
    with open(self.best_config_file_path, "w") as f:
      json.dump(self.best_config, f)

class SmacCallerStatic(SmacCaller):
  def __init__(self, size, experiment_multiple, seed):
    super().__init__("static", size, experiment_multiple, seed)

  def config(self):
    def runner(x, seed=0):
      lbd = x["lbd"]
      _, _, quality = onell_lambda(self.size, lbds=[lbd]*self.size, seed=seed)
      return quality 
    self.runner = runner
    lbd = UniformIntegerHyperparameter("lbd", 1, self.size-1)
    self.cs.add_hyperparameters([lbd])
    super().config()

  def parse_result(self):
    self.best_config = [self.best_config_dict["lbd"] for _ in range(self.size)]

class SmacCallerDynamic(SmacCaller):
  def __init__(self, size, experiment_multiple, seed):
    super().__init__("dynamic", size, experiment_multiple, seed)

  def config(self):
    def runner(x, seed=0):
      lbds = [None] * self.size
      for i in range(self.size):
        lbds[i] = x[f"lbd{i}"]
      _, _, quality = onell_lambda(self.size, lbds=lbds, seed=seed)
      return quality 
    self.runner = runner
    self.cs.add_hyperparameters([UniformIntegerHyperparameter(f"lbd{i}", 1, self.size-1) for i in range(self.size)])
    super().config()
  
  def parse_result(self):
    self.best_config = [self.best_config_dict[f"lbd{i}"] for i in range(self.size)]


class SCDynamicBin(SmacCaller):
  def __init__(self, size, experiment_multiple, seed):
    self.bins = []
    self.bin_lookup = []
    remaining = size
    bin_size = int(size * first_bin_portion)
    i = 0
    while remaining:
      self.bins.append(bin_size)
      remaining -= bin_size
      for _ in range(bin_size):
        self.bin_lookup.append(i)
      bin_size = int(bin_size / descent_rate)
      if bin_size < 1:
        bin_size = 1
      i += 1
    super().__init__("dynamic_bin", size, experiment_multiple, seed)

  def config(self):
    def runner(x, seed=0):
      lbds = []
      for i in range(self.size):
        lbds.append(x[f"bin{self.bin_lookup[i]}"])
      _, _, quality = onell_lambda(self.size, lbds=lbds, seed=seed)
      return quality 
    self.runner = runner
    self.cs.add_hyperparameters([UniformIntegerHyperparameter(f"bin{i}", 1, self.size-1) for i in range(len(self.bins))])
    super().config()

  def parse_result(self):
    self.best_config = [self.best_config_dict[f"bin{self.bin_lookup[i]}"] for i in range(self.size)]


def onell_lambda_positional(size, lbds, seed):
  _, _, performance = onell_lambda(size, lbds=lbds, seed=seed)
  return performance

def onell_dynamic_5params_positional(size, seed): 
  _, _, performance = onell_dynamic_5params(size, seed=seed)
  return performance

def onell_dynamic_theory_positional(size, seed):
  _, _, performance = onell_dynamic_theory(size, seed=seed)
  return performance


def run_smac(type: OnellType, size, experiment_multiple, seed):
  if type == OnellType.dynamic:
    smac_caller = SmacCallerDynamic(size, experiment_multiple, seed)
  elif type == OnellType.static:
    smac_caller = SmacCallerStatic(size, experiment_multiple, seed)
  elif type == OnellType.dynamic_bin:
    smac_caller = SCDynamicBin(size, experiment_multiple, seed)
  else:
    raise NotImplementedError("Unknown OneLL type to run")
  smac_caller.run()
  return smac_caller.best_config

def find_performancess(size, runs, seeds, pool):
  return [
    pool.starmap_async(onell_lambda_positional, zip([size]*trials, [best_config]*trials, seeds)) 
    for best_config in runs.get()
  ]

def graph(json_path, png_path, dynamic_lbd_performance, dynamic_lbd_bin_performance, static_lbd_performance, random_dynamic_lbd_performance, random_static_lbd_performance, one_lbd_performance, dynamic_theory_performance, dynamic_5params_performance):
  data = (dynamic_lbd_performance, dynamic_lbd_bin_performance, static_lbd_performance, random_dynamic_lbd_performance, random_static_lbd_performance, one_lbd_performance, dynamic_theory_performance, dynamic_5params_performance)
  with open(json_path, 'w') as f:
    json.dump(data, f)
  figure, ax = plt.subplots(figsize=(12,5))
  figure.subplots_adjust(left=0.25)
  ax.boxplot(data, labels=("Dynamic Lambda", "Dynamic Lambda with binning", "Static Lambda", "Random Dynamic Lambda", "Random Static Lambda", "Lambda = 1", "Dynamic Theory", "Five Parameters"), vert=False)
  figure.savefig(png_path, dpi=300)
  
def find_best_performances_i(performancess):
  performancess = [performances.get() for performances in performancess.get()]
  return np.argmin(np.mean(performancess, axis=1))

def main(i):
  logging.info(f"config: i = {i}, size = {sizes[i]}, experiment_multiple_dynamic = {experiment_multiples_dynamic[i]}, experiment_multiple_static = {experiment_multiples_static[i]}, smac_instances = {smac_instances}")
  pool = Pool(threads)
  tpool = ThreadPool()
  Path("smac_output").mkdir(exist_ok=True, parents=True)
  rng = np.random.default_rng(seed*i)
  dynamic_bin_runs = pool.starmap_async(run_smac, [(
      OnellType.dynamic_bin, 
      sizes[i], 
      experiment_multiples_dynamic[i] // smac_instances, 
      rng.integers(1<<15, (1<<16)-1), 
    ) for _ in range(threads)]
  )
  dynamic_runs = pool.starmap_async(run_smac, [(
      OnellType.dynamic, 
      sizes[i], 
      experiment_multiples_dynamic[i] // smac_instances, 
      rng.integers(1<<15, (1<<16)-1), 
    ) for _ in range(threads)]
  )
  static_runs = pool.starmap_async(run_smac, [
    (
      OnellType.static,
      sizes[i],
      experiment_multiples_static[i] // smac_instances,
      rng.integers(1<<15, (1<<16)-1), 
    ) for _ in range(threads)]
  )

  performancess_dynamic = tpool.apply_async(find_performancess, (sizes[i], dynamic_runs, rng.integers(1<<15, (1<<16)-1, trials), pool))
  performancess_dynamic_bin = tpool.apply_async(find_performancess, (sizes[i], dynamic_bin_runs, rng.integers(1<<15, (1<<16)-1, trials), pool))
  performancess_static = tpool.apply_async(find_performancess, (sizes[i], static_runs, rng.integers(1<<15, (1<<16)-1, trials), pool))
  best_performances_dynamic_i = tpool.apply_async(find_best_performances_i, (performancess_dynamic, ))
  best_performances_dynamic_bin_i = tpool.apply_async(find_best_performances_i, (performancess_dynamic_bin, ))
  best_performances_static_i = tpool.apply_async(find_best_performances_i, (performancess_static, ))
  
  random_dynamic_lbd_performance = pool.starmap_async(onell_lambda_positional, zip([sizes[i]]*trials, [list(rng.integers(1, sizes[i], sizes[i])) for _ in range(trials)], rng.integers(1<<15, (1<<16)-1, trials))) 
  random_static_lbd_performance = pool.starmap_async(onell_lambda_positional, zip([sizes[i]]*trials, [[rng.integers(1, sizes[i])]*sizes[i] for _ in range(trials)], rng.integers(1<<15, (1<<16)-1, trials)))  
  one_ldb_performance = pool.starmap_async(onell_lambda_positional, zip([sizes[i]]*trials, [[1]*sizes[i]]*trials, rng.integers(1<<15, (1<<16)-1, trials)))
  dynamic_theory_performance = pool.starmap_async(onell_dynamic_theory_positional, zip([sizes[i]]*trials, rng.integers(1<<15, (1<<16)-1, trials)))
  dynamic_5params_performance = pool.starmap_async(onell_dynamic_5params_positional, zip([sizes[i]]*trials, rng.integers(1<<15, (1<<16)-1, trials)))

  # Can wait for everything from here
  with open(os.path.join("smac_output", f"i_{sizes[i]}_{experiment_multiples_dynamic[i]}_{experiment_multiples_static[i]}.json"), 'w') as f:
    json.dump([dynamic_runs.get()[best_performances_dynamic_i.get()], static_runs.get()[best_performances_static_i.get()]], f)
  
  graph(
    os.path.join("smac_output", f"performance_{sizes[i]}_{experiment_multiples_dynamic[i]}_{experiment_multiples_static[i]}.json"),
    os.path.join("smac_output", f"performance_{sizes[i]}_{experiment_multiples_dynamic[i]}_{experiment_multiples_static[i]}.png"),
    performancess_dynamic.get()[best_performances_dynamic_i.get()].get(),
    performancess_dynamic_bin.get()[best_performances_dynamic_bin_i.get()].get(),
    performancess_static.get()[best_performances_static_i.get()].get(),
    random_dynamic_lbd_performance.get(),
    random_static_lbd_performance.get(),
    one_ldb_performance.get(),
    dynamic_theory_performance.get(),
    dynamic_5params_performance.get(),
  )


  
  tpool.close()
  pool.close()
  pool.join()
  tpool.join()
  return

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("i", type=int)
  parser.add_argument("--binning", action="store_true")
  args = parser.parse_args()
  exit(main(args.i))
