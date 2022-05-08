#! /usr/bin/env python3

import subprocess
from config import N, sizes, experiment_multiples_dynamic, experiment_multiples_static, seed, threads, trials
import numpy
from multiprocessing import Pool
from onell_algs import onell_lambda, onell_dynamic_theory, onell_dynamic_5params
import matplotlib.pyplot as plt
import json 

rng = numpy.random.default_rng(seed)
best_dynamic_config = [None] * N
best_static_config = [None] * N


class IraceDecoder:
  def __init__(self):
    self.lines = []
  
  def note_line(self, line):
    if line.strip().startswith("#"):
      self.lines = []
    else:
      self.lines.append(line)
  
  def end(self):
    line = self.lines[0]
    line = line.strip().split()[1:]
    return [int(line[i]) for i in range(len(line)) if i%2 == 1]

class IraceCaller:
  def __init__(self, size, experiment_multiple, seed, target_runner, output_file, log_file, read_output=False):
    self.size = size
    self.experiment_multiple = experiment_multiple
    self.seed = seed
    self.target_runner = target_runner
    self.output_file = output_file
    self.read_output = read_output
    self.log_file = log_file
  
  def run(self):
    if not self.read_output:
      self.write_parameters()
      self.call_and_record()
    else:
      self.read_from_output()
  def write_parameters(self):
    with open("Instances/1.txt", "w") as f:
      f.write(f"{self.size}\n")

    with open("scenario.txt", "w") as f:
      f.write(f"maxExperiments = {self.size * self.experiment_multiple}\n")
      f.write(f"targetRunner = \"{self.target_runner}\"\n")
      f.write(f"boundMax = 99999999\n")
      f.write(f"boundPar = 2\n")
      f.write(f"testType = \"t-test\"\n")
      f.write(f"firstTest = 10\n")

  def call_and_record(self): 
    output_f = open(self.output_file, 'w') 
    process = subprocess.Popen(["irace", "--parallel", str(threads), "--seed", str(self.seed), "--log-file", self.log_file], stdout=subprocess.PIPE)
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
    self.best_config = decoder.end()

  def read_from_output(self):
    decoder = IraceDecoder()
    with open(self.output_file) as f:
      for line in f:
        decoder.note_line(line)
    self.best_config = decoder.end()

  

class IraceCallerDynamic(IraceCaller):
  def __init__(self, size, experiment_multiple, seed):
      super().__init__(size, experiment_multiple, seed, "./target_runner_dynamic.py", f"output_dynamic_{size}.txt", f"irace_dynmaic_{size}.Rdata")
  
  def write_parameters(self):
    with open("parameters.txt", "w") as f:
      for i in range(self.size):
        f.write(f"lbd{i} \"--lbd{i} \" i (1, {self.size-1}) \n")
    return super().write_parameters()

class IraceCallerStatic(IraceCaller):
  def __init__(self, size, experiment_multiple, seed):
      super().__init__(size, experiment_multiple, seed, "./target_runner_static.py", f"output_static_{size}.txt", f"irace_static_{size}.Rdata")
  
  def write_parameters(self):
    with open("parameters.txt", "w") as f:
      f.write(f"lbd \"--lbd \" i (1, {self.size-1}) \n")
    return super().write_parameters()

def onell_eval(f, n, lbds, seed):
    if lbds:
        res = f(n, lbds=lbds, seed=seed)
    else:
        res = f(n, seed=seed)
    if res[1] != n:
        print(f"Capped with {f}, {n}, {lbds}, {seed}")
    return res[2]

def next_seeds(size):
    res = list(rng.integers(low=10**10, high=10**11, size=size))
    return res

def graph(n, static_lbd, dynamic_lbd, pool, read_json=False):
  if not read_json:
    random_lbd_set = [list(rng.integers(low=1, high=n, size=n)) for _ in range(trials)]
    random_lbd = list(rng.integers(low=1, high=n, size=n))
    static_lbd_performace = pool.starmap(onell_eval, zip([onell_lambda]*trials, [n]*trials, [static_lbd]*trials, next_seeds(trials)))
    dynamic_lbd_performace = pool.starmap(onell_eval, zip([onell_lambda]*trials, [n]*trials, [dynamic_lbd]*trials, next_seeds(trials)))
    random_lbd_performace = pool.starmap(onell_eval, zip([onell_lambda]*trials, [n]*trials, random_lbd_set, next_seeds(trials)))
    random_lbd_same_performace = pool.starmap(onell_eval, zip([onell_lambda]*trials, [n]*trials, [random_lbd]*trials, next_seeds(trials)))
    one_lbd_performace = pool.starmap(onell_eval, zip([onell_lambda]*trials, [n]*trials, [[1]*n]*trials, next_seeds(trials)))
    dynamic_theory_performace = pool.starmap(onell_eval, zip([onell_dynamic_theory]*trials, [n]*trials, [None]*trials, next_seeds(trials)))
    five_param_performace = pool.starmap(onell_eval, zip([onell_dynamic_5params]*trials, [n]*trials, [None]*trials, next_seeds(trials)))
    with open(f"performace_{n}.json", "w") as f:
      json.dump((static_lbd_performace, dynamic_lbd_performace, random_lbd_performace, random_lbd_same_performace, one_lbd_performace, dynamic_theory_performace, five_param_performace), f)
  else:
    with open(f"performace_{n}.json") as f:
      static_lbd_performace, dynamic_lbd_performace, random_lbd_performace, random_lbd_same_performace, one_lbd_performace, dynamic_theory_performace, five_param_performace = json.load(f)
    figure, ax = plt.subplots(figsize=(12,5))
    figure.subplots_adjust(left=0.25)
    ax.boxplot((static_lbd_performace, dynamic_lbd_performace, random_lbd_performace, random_lbd_same_performace, one_lbd_performace, dynamic_theory_performace, five_param_performace), labels=(f"Static Lambda (lbd={5})", "Dynamic Lambda", "Random Lambda (Lambda changes)", "Random Lambda (Lambda fixed)", "Lambda = 1", "Dynamic Theory", "Five Parameters"), vert=False)
    figure.savefig(f'box_plot_{n}.png', dpi=300)
    return 

    

def main():
  global best_dynamic_config
  dynamic_irace_caller: list[IraceCallerDynamic] = [None] * N
  static_irace_caller: list[IraceCallerStatic] = [None] * N
  pool = Pool(threads)
  for i in range(N):
    irace_caller_dynamic = IraceCallerDynamic(sizes[i], experiment_multiples_dynamic[i], rng.integers(1<<15, (1<<16)-1))
    irace_caller_dynamic.run()
    dynamic_irace_caller[i] =irace_caller_dynamic
    irace_caller_static = IraceCallerStatic(sizes[i], experiment_multiples_static[i], rng.integers(1<<15, (1<<16)-1))
    irace_caller_static.run()
    static_irace_caller[i] = irace_caller_static
    graph(sizes[i], static_irace_caller[i].best_config * sizes[i], dynamic_irace_caller[i].best_config, pool)
  pool.close()
  pool.join()


if __name__ == "__main__":
  main()



