import logging

logging.basicConfig(level=logging.INFO)

import numpy as np
import os
from multiprocessing import Pool

from ConfigSpace.hyperparameters import UniformFloatHyperparameter, UniformIntegerHyperparameter

# Import ConfigSpace and different types of parameters
from smac.configspace import ConfigurationSpace
from smac.facade.smac_bb_facade import SMAC4BB

# Import SMAC-utilities
from smac.scenario.scenario import Scenario
from onell_algs import onell_lambda


from config import seed_small as seed, N, sizes, experiment_multiples_dynamic, experiment_multiples_static, threads
from utils import graph
import send_email


rng = np.random.default_rng(seed)

class SmacCaller:
  def __init__(self, type_name, size, experiment_multiple, seed, output_dir="smac_output"):
    self.output_dir = output_dir
    self.size = size
    self.experiment_multiple = experiment_multiple
    self.seed = seed
    self.type_name = type_name
    self.cs = ConfigurationSpace()
    self.runner = None
    self.config()


  def config(self):
    self.scenario = Scenario({
      "shared_model": "true",
      "run_obj": "quality",  # we optimize quality (alternatively runtime)
      "ta_run_limit": self.size*self.experiment_multiple,  # max. number of function calls
      "cs": self.cs,  # configuration space
      "deterministic": "false",
      "output_dir": os.path.join(self.output_dir, f"{self.type_name}_{self.size}_{self.experiment_multiple}")
    })
    self.smac = SMAC4BB(
      scenario=self.scenario,
      rng=np.random.RandomState(self.seed),
      tae_runner=self.runner,
    )

  def run(self):
    self.best_config = self.smac.optimize()

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

def main():
  pool = Pool(threads)
  for i in range(N):
    smac_caller_dynamic = SmacCallerDynamic(sizes[i], experiment_multiples_dynamic[i], rng.integers(1<<15, (1<<16)-1))
    smac_caller_dynamic.run()
    smac_caller_static = SmacCallerStatic(sizes[i], experiment_multiples_static[i], rng.integers(1<<15, (1<<16)-1))
    smac_caller_static.run()
    graph(sizes[i], "smac_output", experiment_multiples_static[i], experiment_multiples_dynamic[i], [smac_caller_static.best_config["lbd"]]*sizes[i], [smac_caller_dynamic.best_config[f"lbd{i}"] for i in range(sizes[i])], rng, pool)
    try:
      send_email.main(f"SMAC: {sizes[i]} Done.")
    except:
      pass



if __name__ == "__main__":
  main()