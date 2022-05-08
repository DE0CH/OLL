#! /usr/bin/env python3

import subprocess
import os
import sys

from black import out
from config import N, sizes, experiment_multiples_dynamic, experiment_multiples_static, seed, threads
import numpy
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
  def __init__(self, size, experiment_multiple, seed, target_runner):
    self.size = size
    self.experiment_multiple = experiment_multiple
    self.seed = seed
    self.target_runner = target_runner
  
  def run(self):
    self.write_parameters()
    self.call_and_record()
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
    output_f = open(f'output_dynamic_{self.size}.txt', 'w') 
    process = subprocess.Popen(["irace", "--parallel", str(threads), "--seed", str(self.seed)], stdout=subprocess.PIPE)
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
    return self.best_config

class IraceCallerDynamic(IraceCaller):
  def __init__(self, size, experiment_multiple, seed):
      super().__init__(size, experiment_multiple, seed, "./target_runner_dynamic.py")
  
  def write_parameters(self):
    with open("parameters.txt", "w") as f:
      for i in range(self.size):
        f.write(f"lbd{i} \"--lbd{i} \" i (1, {self.size-1}) \n")
    return super().write_parameters()

class IraceCallerStatic(IraceCaller):
  def __init__(self, size, experiment_multiple, seed):
      super().__init__(size, experiment_multiple, seed, "./target_runner_static.py")
  
  def write_parameters(self):
    with open("parameters.txt", "w") as f:
      f.write(f"lbd \"--lbd \" i (1, {self.size-1}) \n")
    return super().write_parameters()



def call_irace_dynamic(size, experiment_multiple_dynamic, seed):
  global open_files
  output_f = open(f'output_dynamic_{size}.txt', 'w')
  open_files.add(output_f)
  with open("Instances/1.txt", "w") as f:
    f.write(f"{size}\n")
  with open("parameters.txt", "w") as f:
    for i in range(size):
      f.write(f"lbd{i} \"--lbd{i} \" i (1, {size-1}) \n")
  with open("scenario.txt", "w") as f:
    f.write(f"maxExperiments = {size * experiment_multiple_dynamic}\n")
    f.write("targetRunner = \"./target_runner_dynamic.py\"\n")
    f.write(f"boundMax = 99999999\n")
    f.write(f"boundPar = 2\n")
    f.write(f"testType = \"t-test\"\n")
    f.write(f"firstTest = 10\n")
  process = subprocess.Popen(["irace", "--parallel", str(threads), "--seed", str(seed)], stdout=subprocess.PIPE)

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
  open_files.remove(output_f)
  return decoder.end()

def call_irace_static(size, experiment_multiple_static, seed):
  global open_files
  output_f = open(f'output_static_{size}.txt', 'w')
  open_files.add(output_f)


def main():
  global best_dynamic_config
  dynamic_irace_caller: list[IraceCallerDynamic] = [None] * N
  static_irace_caller: list[IraceCallerStatic] = [None] * N
  for i in range(N):
    irace_caller = IraceCallerDynamic(sizes[i], experiment_multiples_dynamic[i], rng.integers(1<<15, (1<<16)-1))
    irace_caller.run()
    dynamic_irace_caller[i] =irace_caller
  for i in range(N):
    irace_caller = IraceCallerStatic(sizes[i], experiment_multiples_dynamic[i], rng.integers(1<<15, (1<<16)-1))
    irace_caller.run()
    static_irace_caller[i] = irace_caller
  for i in range(N):
    print(static_irace_caller[i].best_config)
    print(dynamic_irace_caller[i].best_config)
  



if __name__ == "__main__":

  main()


