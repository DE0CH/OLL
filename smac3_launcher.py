import logging

logging.basicConfig(level=logging.ERROR)

import numpy as np
import os
from multiprocessing.pool import Pool

from ConfigSpace.hyperparameters import UniformFloatHyperparameter, UniformIntegerHyperparameter

# Import ConfigSpace and different types of parameters
from smac.configspace import ConfigurationSpace
from smac.facade.smac_bb_facade import SMAC4BB
from smac.facade.smac_ac_facade import SMAC4AC

# Import SMAC-utilities
from smac.scenario.scenario import Scenario
from onell_algs import onell_lambda


from config import seed_small as seed, N, sizes, experiment_multiples_dynamic, experiment_multiples_static, threads, EMAIL, trials, smac_instances
from utils import graph
import send_email
import socket
import json
import argparse
import asyncio
from dataclasses import dataclass

@dataclass
class OnellType:
  dynamic = 1
  static = 2

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
      "ta_run_limit": self.size*self.experiment_multiple,  # max. number of function calls
      "cs": self.cs,  # configuration space
      "deterministic": "false",
      "output_dir": os.path.join(self.output_dir, f"{self.type_name}_{self.size}_{self.experiment_multiple}")
    })
    self.smac = SMAC4AC(
      scenario=self.scenario,
      rng=np.random.RandomState(self.seed),
      tae_runner=self.runner,
    )

  def parse_result(self):
    raise NotImplementedError()

  def run(self):
    if os.path.isfile(self.best_config_file_path):
      with open(self.best_config_file_path) as f:
        self.best_config = json.load(f)
    else:
      self.config()
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

def onell_lambda_positional(size, lbds, seed):
  _, _, performance = onell_lambda(size, lbds=lbds, seed=seed)
  return performance

async def evaluate_smac(type, size, experiment_multiple, seed, seeds, pool: Pool):
  best_config = pool.apply_async(run_smac, (type, size, experiment_multiple, seed))
  best_config = best_config.get()
  file_path = os.path.join("smac_output", f"performances_{type}_{size}_{experiment_multiple}_{seed}.json")
  try:
    with open(file_path) as f:
      performances = json.load(f)
  except (FileNotFoundError, json.decoder.JSONDecodeError):
    performances = pool.starmap(onell_lambda_positional, zip([size]*trials, [best_config]*trials, seeds))
    performances = list(performances)
    with open(file_path, 'w') as f:
      json.dump(performances, f)
  return best_config, performances

def run_smac(type: OnellType, size, experiment_multiple, seed):
  if type == OnellType.dynamic:
    smac_caller = SmacCallerDynamic(size, experiment_multiple, seed)
  elif type == OnellType.static:
    smac_caller = SmacCallerStatic(size, experiment_multiple, seed)
  else:
    raise NotImplementedError("Unknown OneLL type to run")
  smac_caller.run()
  return smac_caller.best_config

async def find_best_config(runs):
  runs = [await run for run in runs]
  configs = [config for config, performances in runs]
  performancess = [performances for config, performances in runs]
  i = np.argmin(np.mean(performancess, axis=1))
  return configs[i], performancess[i]


async def main(i):
  pool = Pool(threads)
  rng = np.random.default_rng(seed)
  dynamic_runs = [asyncio.create_task(
    evaluate_smac(
      OnellType.dynamic, 
      sizes[i], 
      experiment_multiples_dynamic[i], 
      rng.integers(1<<15, (1<<16)-1), 
      rng.integers(1<<15, (1<<16)-1, trials),
      pool
    )
  ) for _ in range(threads)]
  static_runs = [asyncio.create_task(
    evaluate_smac(
      OnellType.static,
      sizes[i],
      experiment_multiples_static[i],
      rng.integers(1<<15, (1<<16)-1), 
      rng.integers(1<<15, (1<<16)-1, trials),
      pool
    )
  ) for _ in range(threads)] 
  best_config_dynamic = asyncio.create_task(find_best_config(dynamic_runs))
  best_config_static = asyncio.create_task(find_best_config(static_runs))
  best_config_dynamic, performances_dynamics = await best_config_dynamic
  best_config_static, performances_static = await best_config_static

  graph(sizes[i], "smac_output", experiment_multiples_dynamic[i], experiment_multiples_static[i], best_config_dynamic, best_config_static, rng, pool)
  if EMAIL:
    try:
      send_email.main(f"SMAC: {sizes[i]} Done on {socket.gethostname()}.")
    except:
      pass


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("i", type=int)
  args = parser.parse_args()

  asyncio.run(main(args.i))