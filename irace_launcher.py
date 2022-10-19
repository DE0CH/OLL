#! /usr/bin/env python3

import subprocess
from config import N, flatten_lbds, sizes, experiment_multiples_dynamic, experiment_multiples_static, seed, threads, trials, descent_rates, get_bins, get_cutoff, default_lbds, sizes_reverse
import numpy
from multiprocessing import Pool
from onell_algs import onell_lambda, onell_dynamic_theory, onell_dynamic_5params
import matplotlib.pyplot as plt
import json 
from pathlib import Path
import os
from utils import graph as _graph
import argparse
import shutil
from decoder import IraceDecoder

rng = numpy.random.default_rng(seed)
best_dynamic_config = [None] * N
best_static_config = [None] * N


class IraceCaller:
  def __init__(self, size, experiment_multiple, seed, type_name, configuration_file=None, extra_names=''):
    Path("irace_output").mkdir(parents=True, exist_ok=True)
    Path(f"irace_output/Instances_{size}{extra_names}").mkdir(parents=True, exist_ok=True)
    self.size = size
    self.experiment_multiple = experiment_multiple
    self.seed = seed
    self.target_runner = f"target_runner_{type_name}.py"
    self.output_file = f"irace_output_{type_name}_{size}_{experiment_multiple}{extra_names}_{seed}.txt"
    self.read_output = os.path.isfile(f"irace_output/{self.output_file}")
    self.log_file = f"irace_{type_name}_{size}_{experiment_multiple}{extra_names}_{seed}.Rdata"
    self.parameters_file = f"irace_output/parameters_{type_name}{extra_names}_{size}.txt"
    self.type_name = type_name
    self.irace_bin_path = os.path.join(subprocess.check_output(['Rscript', '-e', "cat(system.file(package=\'irace\', \'bin\', mustWork=TRUE))"]).decode('utf-8'), 'irace')
    self.instance_dir = f"Instances_{self.size}{extra_names}"
    self.configurations_file = configuration_file
    self.extra_names = extra_names
  
  def run(self):
    if not self.read_output:
      self.write_parameters()
      self.call_and_record()
      self.translate()
    else:
      try:
        self.read_from_output()
        self.translate()
        if len(self.best_config) != self.size:
          raise ValueError("Incorrect best config size")
      except: # corrupt data, try to recover
        self.write_parameters()
        self.call_and_record()
        self.translate()

  
  def write_parameters(self):
    with open(f"irace_output/{self.instance_dir}/1.txt", "w") as f:
      f.write(f"{self.size}\n")
      if self.extra_names:
        f.write(f'{self.extra_names}\n')

    with open(f"irace_output/scenario_{self.type_name}_{self.size}_{self.experiment_multiple}{self.extra_names}_{self.seed}.txt", "w") as f:
      f.write(f"maxExperiments = {self.size * self.experiment_multiple}\n")
      f.write(f"targetRunner = \"{os.path.join('..', self.target_runner)}\"\n")
      f.write(f"boundMax = 99999999\n")
      f.write(f"boundPar = 2\n")
      f.write(f"testType = \"t-test\"\n")
      f.write(f"firstTest = 10\n")
      if self.configurations_file:
        f.write(f"configurationsFile = \"{os.path.basename(self.configurations_file)}\"")

  def call_and_record(self, read_recovery=True): 
    output_f = open(f"irace_output/{self.output_file}.progress", 'w') 
    args = [
      "--parallel", str(threads), 
      "--seed", str(self.seed), 
      "--capping", "1",
      "--bound-max", str(get_cutoff(self.size)),
      "--log-file", f"{self.log_file}", 
      "--scenario", f"scenario_{self.type_name}_{self.size}_{self.experiment_multiple}{self.extra_names}_{self.seed}.txt", 
      "--train-instances-dir", self.instance_dir,
      "--parameter-file", os.path.basename(self.parameters_file)
    ]
    if os.path.isfile(f'irace_output/{self.log_file}') and read_recovery:
      shutil.copyfile(f'irace_output/{self.log_file}', f'irace_output/{self.log_file}.progress')
      args += ['--recovery-file', f'{self.log_file}.progress']
    process = subprocess.Popen([self.irace_bin_path] + args,
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
    process.wait()
    if process.returncode != 0:
      raise ChildProcessError("irace had non zero return code")
    output_f.close()
    os.rename(f"irace_output/{self.output_file}.progress", f"irace_output/{self.output_file}")
    try:
      self.best_config = decoder.end()
    except:
      self.call_and_record(read_recovery=False)
    finally:
      if os.path.isfile(f'irace_output/{self.log_file}.progress'):
        os.remove(f'irace_output/{self.log_file}.progress')

  def read_from_output(self):
    decoder = IraceDecoder()
    with open(f"irace_output/{self.output_file}") as f:
      for line in f:
        decoder.note_line(line)
    self.best_config = decoder.end()

  def translate(self):
    pass


class IraceCallerDynamic(IraceCaller):
  def __init__(self, size, experiment_multiple, seed, type_name="dynamic"):
      super().__init__(size, experiment_multiple, seed, type_name)
  
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
  def __init__(self, size, experiment_multiple, descent_rate_j, seed, type_name="binning_comparison"):
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

def write_default_parameters(self, length):
  with open(f"irace_output/{self.configurations_file}", 'w') as f:
    row_lengths = []
    for i in range(length):
      row_length = max(len(f"{self.default_value:.3f}"), len(f"lbd{i}"))
      row_lengths.append(row_length)
      f.write(f"lbd{i}")
      f.write(' ' * (row_length - len(f"lbd{i}") + 1))
    f.write('\n')
    for i in range(length):
      f.write(f"{self.default_value:.3f}")
      f.write(' ' * (row_lengths[i] - len(f"{self.default_value:.3f}") + 1))

def write_default_parameters_for_lbds(configurations_file, lbds):
  length = len(lbds)
  with open(f"irace_output/{configurations_file}", "w") as f:
    row_lengths = []
    for i in range(length):
      row_length = max(len(f"{lbds[i]}"), len(f"lbd{i}"))
      row_lengths.append(row_length)
      f.write(f"lbd{i}")
      f.write(' ' * (row_length - len(f"lbd{i}") + 1))
    f.write('\n')
    for i in range(length):
      f.write(f"{lbds[i]}")
      f.write(' ' * (row_lengths[i] - len(f"{lbds[i]}") + 1))
    f.write('\n')

class IraceCallerBinningComparisonWithStatic(IraceCallerBinningComparison):
  def __init__(self, size, experiment_multiple, descent_rate_j, seed, type_name="binning_comparison_with_static"):
    descent_rate = descent_rates[descent_rate_j]
    default_value = default_lbds[sizes_reverse[size]]
    self.default_value = default_value
    super().__init__(size, experiment_multiple, descent_rate_j, seed, type_name=type_name)
    self.configurations_file = f"configurations_{type_name}_{size}_{experiment_multiple}_{descent_rate}_{default_value}_{seed}.txt"

  def write_parameters(self):
    write_default_parameters(self, len(self.bins))
    return super().write_parameters()

class IraceCallerDynamicWithStatic(IraceCallerDynamic):
  def __init__(self, size, experiment_multiple, seed, type_name="dynamic_with_static"):
    default_value = default_lbds[sizes_reverse[size]]
    self.default_value = default_value
    super().__init__(size, experiment_multiple, seed, type_name)
    self.configurations_file = f"configurations_{type_name}_{size}_{experiment_multiple}_{default_value}_{seed}.txt"

  def write_parameters(self):
    write_default_parameters(self, self.size)
    return super().write_parameters()

class IraceCallerBinningWithDefaults(IraceCaller):
  def __init__(self, size, i, experiment_multiple, default_lbds, bins, seed, type_name="binning_with_defaults"):
    # default lbds is the flattened value, it will convert to the binned ones before passing to irace
    type_name = type_name
    self.type_name = type_name
    self.default_lbds = default_lbds
    self.bins = bins
    self.target_runner = f"irace_out/target_runner_{type_name}.py"
    if default_lbds is not None:
      super().__init__(size, experiment_multiple, seed, type_name, configuration_file=f"configurations_{type_name}_{size}_{experiment_multiple}_{i}_{seed}.txt", extra_names="_" + str(i))
    else:
      super().__init__(size, experiment_multiple, seed, type_name, extra_names="_" + str(i))

  def write_parameters(self):  
    with open(self.parameters_file, "w") as f:
      for i in range(len(self.bins)-1):
        f.write(f"lbd{i} \"--lbd{i} \" r (1, {self.size}) \n")
    if self.default_lbds is not None:
      binned_lbds = []
      for j in range(len(self.bins)-1):
        binned_lbds.append(self.default_lbds[self.bins[j]])
      write_default_parameters_for_lbds(self.configurations_file, binned_lbds)
    return super().write_parameters()
  
  def translate(self):
    self.best_config = flatten_lbds(self.best_config, self.bins)
    return super().translate()
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



