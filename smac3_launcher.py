import logging

logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s', level=logging.DEBUG)

logging.debug("Importing statement")
import numpy as np
import os
from multiprocessing.pool import Pool, AsyncResult
import asyncio

from ConfigSpace.hyperparameters import UniformIntegerHyperparameter

# Import ConfigSpace and different types of parameters
from smac.configspace import ConfigurationSpace
from smac.facade.smac_ac_facade import SMAC4AC

# Import SMAC-utilities
from smac.scenario.scenario import Scenario
from onell_algs import onell_lambda


from config import seed_small as seed, N, sizes, experiment_multiples_dynamic, experiment_multiples_static, threads, EMAIL, trials, smac_instances
import json
import argparse
logging.debug("Finished Importing")


class SmacCaller:
  def __init__(self, type_name, size, experiment_multiple, seed, pool, output_dir="smac_output"):
    self.output_dir = output_dir
    self.size = size
    self.experiment_multiple = experiment_multiple
    self.seed = seed
    self.type_name = type_name
    self.cs = ConfigurationSpace()
    self.pool: Pool = pool
    self.runner = None
    self.best_config_dict_result: AsyncResult = None
    self.best_config = None
    self.best_config_file_path = os.path.join(self.output_dir, f"best_config_{self.type_name}_{self.size}_{self.experiment_multiple}_{seed}.json")


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

  def run_async(self):
    if os.path.isfile(self.best_config_file_path):
      with open(self.best_config_file_path) as f:
        self.best_config = json.load(f)
    else:
      self.config()
      self.best_config_dict_result = self.pool.apply_async(self.smac.optimize)


  def get_best_config(self):
    if self.best_config is not None:
      return self.best_config
    else:
      best_config_dict = self.best_config_dict_result.get()
      self.best_config = [best_config_dict[f"lbd{i}"] for i in range(self.size)]
      with open(self.best_config_file_path, "w") as f:
        json.dump(self.best_config, f)
      return self.best_config


class SmacCallerStatic(SmacCaller):
  def __init__(self, size, experiment_multiple, seed, pool):
    super().__init__("static", size, experiment_multiple, seed, pool)

  def config(self):
    def runner(x, seed=0):
      lbd = x["lbd"]
      _, _, quality = onell_lambda(self.size, lbds=[lbd]*self.size, seed=seed)
      return quality 
    self.runner = runner
    lbd = UniformIntegerHyperparameter("lbd", 1, self.size-1)
    self.cs.add_hyperparameters([lbd])
    super().config()

class SmacCallerDynamic(SmacCaller):
  def __init__(self, size, experiment_multiple, seed, pool):
    super().__init__("dynamic", size, experiment_multiple, seed, pool)

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

class OnellEvaluator():
  def __init__(self, smac_caller: SmacCaller, seed, pool: Pool):
    self.smac_caller: SmacCaller = smac_caller
    self.seed = seed
    self.pool: Pool = pool
    self.performance_result = None
    self.performance = None
  def run_async(self):
    if isinstance(self.smac_caller, SmacCallerDynamic):  
      lbds = self.smac_caller.get_best_config()
    elif isinstance(self.smac_caller, SmacCallerStatic):
      lbds = self.smac_caller.get_best_config() * self.smac_caller.size
    else:
      raise NotImplementedError("Unknown SmacCaller Type")
    self.performance_result = self.pool.apply_async(onell_lambda, (self.smac_caller.size, ), {'seed': self.seed, 'lbds': lbds})
  def get_performance(self):
    if self.performance is not None:
      return self.performance
    else:
      self.performance = self.performance_result.get()
      return self.performance

def randints(rng, n):
  return rng.integers(1<<15, (1<<16)-1, n)

def randint(rng):
  return rng.integers(1<<15, (1<<16)-1)

async def main(i):
  pool = Pool(threads)
  rng = np.random.default_rng(seed)
  smac_dynamic_callers = [SmacCallerDynamic(sizes[i], experiment_multiples_dynamic[i], randint(rng), pool) for _ in range(smac_instances)]
  [caller.run_async() for caller in smac_dynamic_callers]

  smac_static_callers = [SmacCallerStatic(sizes[i], experiment_multiples_static[i], randint(rng), pool) for _ in range(smac_instances)]
  [caller.run_async() for caller in smac_static_callers]

  performances_dynamic = [[OnellEvaluator(smac_dynamic_caller, randint(rng), pool) for _ in range(trials)] for smac_dynamic_caller in smac_dynamic_callers]
  [[evaluator.run_async() for evaluator in performance_dynamic] for performance_dynamic in performances_dynamic]

  performances_static = [[OnellEvaluator(smac_static_caller, randint(rng), pool) for _ in range(trials)] for smac_static_caller in smac_static_callers]
  [[evaluator.run_async() for evaluator in performance_static] for performance_static in performances_static]

  best_performance_dynamic_i = np.argmin(np.mean([[evaluator.get_performance() for evaluator in performances_dynamic] for _ in smac_static_callers], axis=1))
  best_performance_static_i = np.argmin(np.mean([[evaluator.get_performance() for evaluator in performances_static] for _ in smac_static_callers]))
  best_performance_dynamic: SmacCallerDynamic = smac_dynamic_callers[best_performance_dynamic_i]
  best_performance_static: SmacCallerStatic = smac_static_callers[best_performance_static_i]

  print(best_performance_dynamic.get_best_config())
  print(best_performance_static.get_best_config())

if __name__ == "__main__":
  argparser = argparse.ArgumentParser()
  argparser.add_argument('i', type=int)
  args = argparser.parse_args()
  i = args.i
  asyncio.run(main(i))