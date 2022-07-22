#! /usr/bin/env python3

import subprocess
from config import N, sizes, experiment_multiples_dynamic, experiment_multiples_static, seed, threads, trials, descent_rates, get_bins, get_cutoff
import numpy
from multiprocessing import Pool
from onell_algs import onell_lambda, onell_dynamic_theory, onell_dynamic_5params
import matplotlib.pyplot as plt
import json 
from pathlib import Path
import os
from utils import graph as _graph
import argparse

rng = numpy.random.default_rng(seed)
best_dynamic_config = [None] * N
best_static_config = [None] * N


class IraceDecoder:
  def __init__(self):
    self.lines = []
  
  def note_line(self, line):
    if line.strip().startswith("# Best configurations as commandlines"):
      self.lines = []
    else:
      self.lines.append(line)
  
  def end(self):
    line = self.lines[0]
    line = line.strip().split()[1:]
    return [float(line[i]) for i in range(len(line)) if i%2 == 1]

class IraceCaller:
  def __init__(self, size, experiment_multiple, seed, type_name):
    Path("irace_output").mkdir(parents=True, exist_ok=True)
    Path(f"irace_output/Instances_{size}").mkdir(parents=True, exist_ok=True)
    self.size = size
    self.experiment_multiple = experiment_multiple
    self.seed = seed
    self.target_runner = f"target_runner_{type_name}.py"
    self.output_file = f"irace_output_{type_name}_{size}_{experiment_multiple}_{seed}.txt"
    self.read_output = os.path.isfile(f"irace_output/{self.output_file}")
    self.log_file = f"irace_{type_name}_{size}_{experiment_multiple}_{seed}.Rdata"
    self.parameters_file = f"irace_output/parameters_{type_name}_{size}.txt"
    self.type_name = type_name
    self.irace_bin_path = os.path.join(subprocess.check_output(['Rscript', '-e', "cat(system.file(package=\'irace\', \'bin\', mustWork=TRUE))"]).decode('utf-8'), 'irace')
    self.instance_dir = f"Instances_{self.size}"
  
  def run(self):
    if not self.read_output:
      self.write_parameters()
      self.call_and_record()
    else:
      self.read_from_output()
    self.translate()
  
  def write_parameters(self):
    with open(f"irace_output/{self.instance_dir}/1.txt", "w") as f:
      f.write(f"{self.size}\n")

    with open(f"irace_output/scenario_{self.type_name}_{self.size}_{self.experiment_multiple}_{self.seed}.txt", "w") as f:
      f.write(f"maxExperiments = {self.size * self.experiment_multiple}\n")
      f.write(f"targetRunner = \"{os.path.join('..', self.target_runner)}\"\n")
      f.write(f"boundMax = 99999999\n")
      f.write(f"boundPar = 2\n")
      f.write(f"testType = \"t-test\"\n")
      f.write(f"firstTest = 10\n")

  def call_and_record(self): 
    output_f = open(f"irace_output/{self.output_file}.progress", 'w') 
    process = subprocess.Popen([self.irace_bin_path, 
      "--parallel", str(threads), 
      "--seed", str(self.seed), 
      "--capping", "1",
      "--bound-max", str(get_cutoff(self.size)),
      "--log-file", f"{self.log_file}", 
      "--scenario", f"scenario_{self.type_name}_{self.size}_{self.experiment_multiple}_{self.seed}.txt", 
      "--train-instances-dir", self.instance_dir,
      "--parameter-file", os.path.basename(self.parameters_file)],
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd="irace_output")
    decoder = IraceDecoder()
    while True:
      try:
        line = next(process.stdout)
        line = line.decode("UTF-8")
        decoder.note_line(line)
        print(line, end="")
        output_f.write(line)
      except StopIteration:
        break
    output_f.close()
    os.rename(f"irace_output/{self.output_file}.progress", f"irace_output/{self.output_file}")
    self.best_config = decoder.end()

  def read_from_output(self):
    decoder = IraceDecoder()
    with open(f"irace_output/{self.output_file}") as f:
      for line in f:
        decoder.note_line(line)
    self.best_config = decoder.end()

  def translate(self):
    pass


class IraceCallerDynamic(IraceCaller):
  def __init__(self, size, experiment_multiple, seed):
      super().__init__(size, experiment_multiple, seed, "dynamic")
  
  def write_parameters(self):
    with open(self.parameters_file, "w") as f:
      for i in range(self.size):
        f.write(f"lbd{i} \"--lbd{i} \" r (1, {self.size}) \n")
    return super().write_parameters()

class IraceCallerStatic(IraceCaller):
  def __init__(self, size, experiment_multiple, seed):
      super().__init__(size, experiment_multiple, seed, "static")
  
  def write_parameters(self):
    with open(self.parameters_file, "w") as f:
      f.write(f"lbd \"--lbd \" r (1, {self.size}) \n")
    return super().write_parameters()
  
  def translate(self):
    lbd_static = self.best_config[0]
    self.best_config = [lbd_static] * self.size
    

class IraceCallerDynamicBin(IraceCaller):
  def __init__(self, size, experiment_multiple, seed):
      super().__init__(size, experiment_multiple, seed, "dynamic_bin")
  
  def write_parameters(self):
    bins, bin_lookup = get_bins(self.size)
    with open(self.parameters_file, "w") as f:
      for i in range(len(bins)):
        f.write(f"lbd{i} \"--lbd{i} \" r (1, {self.size}) \n")
    return super().write_parameters()
  
  def translate(self):
    bins, bin_lookup = get_bins(self.size)
    lbd_bins = self.best_config.copy()
    self.best_config = [1] * self.size
    for i in range(self.size):
      self.best_config[i] = lbd_bins[bin_lookup[i]]
  
class IraceCallerBinningComparison(IraceCaller):
  def __init__(self, size, experiment_multiple, descent_rate_j, seed):
    type_name = "binning_comparison"
    super().__init__(size, experiment_multiple, seed, type_name=type_name)
    self.descent_rate_j = descent_rate_j
    descent_rate = descent_rates[descent_rate_j]
    self.descent_rate = descent_rate
    self.output_file = f"irace_output_{type_name}_{size}_{experiment_multiple}_{descent_rate}_{seed}.txt"
    self.log_file = f"irace_{type_name}_{size}_{experiment_multiple}_{descent_rate}_{seed}.Rdata"
    self.parameters_file = f"irace_output/parameters_{type_name}_{size}_{descent_rate}.txt"
    self.read_output = os.path.isfile(f"irace_output/{self.output_file}")
    self.instance_dir = f"Instances_{size}_{descent_rate}"
    self.bins, self.bin_lookup = get_bins(size, descent_rate=descent_rate)
    Path(f"irace_output/{self.instance_dir}").mkdir(parents=True, exist_ok=True)
  
  def write_parameters(self):
    with open(self.parameters_file, 'w') as f:
      for i in range(len(self.bins)):
        f.write(f"lbd{i} \"--lbd{i} \" r (1, {self.size}) \n")
    super().write_parameters()
    with open(f"irace_output/{self.instance_dir}/1.txt", "a") as f:
      f.write(f"{self.descent_rate_j}\n")

  def translate(self):
    lbd_bins = self.best_config.copy()
    self.best_config = [1] * self.size
    for i in range(self.size):
      self.best_config[i] = lbd_bins[self.bin_lookup[i]]

def onell_eval(f, n, lbds, seed):
    if lbds:
        res = f(n, lbds=lbds, seed=seed)
    else:
        res = f(n, seed=seed)
    if res[1] != n:
        print(f"Capped with {f}, {n}, {lbds}, {seed}")
    return res[2]

def graph(n, static_multiple, dynamic_multiple, static_lbd, dynamic_lbd, pool):
  _graph(n, "irace_output", static_multiple, dynamic_multiple, static_lbd, dynamic_lbd, rng, pool)

def main(i):
  global best_dynamic_config
  dynamic_irace_caller: list[IraceCallerDynamic] = [None] * N
  static_irace_caller: list[IraceCallerStatic] = [None] * N
  pool = Pool(threads)
  irace_caller_dynamic = IraceCallerDynamic(sizes[i], experiment_multiples_dynamic[i], rng.integers(1<<15, (1<<16)-1))
  irace_caller_dynamic.run()
  dynamic_irace_caller[i] = irace_caller_dynamic
  irace_caller_static = IraceCallerStatic(sizes[i], experiment_multiples_static[i], rng.integers(1<<15, (1<<16)-1))
  irace_caller_static.run()
  static_irace_caller[i] = irace_caller_static
  graph(sizes[i], experiment_multiples_dynamic[i], experiment_multiples_static[i], static_irace_caller[i].best_config * sizes[i], dynamic_irace_caller[i].best_config, pool)
  pool.close()
  pool.join()


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument('i', type=int)
  args = parser.parse_args()
  exit(main(args.i))



