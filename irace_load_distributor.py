from ast import arg
import subprocess
import threading
from threading import Thread
import pathlib
from config import graph, seed, N, M
import numpy
import argparse
import os
from enum import Enum 
from uuid import uuid4
from queue import Queue
from threading import Event
import functools
import logging
import time
import sys

rng = numpy.random.default_rng(seed)
job_queue = Queue()
no_op = False

class JobType(Enum):
  baseline = 'baseline'
  binning = 'binning'
  binning_with_static = 'binning_with_static'
  dynamic_with_static = 'dynamic_with_static'
  full = 'full'
  def __str__(self):
    return self.value

def worker(name):
  while True:

    print(f"{name} waiting for job")
    s, cv = job_queue.get()
    print(f"got job: {s}")
    print(f"running {s}")
    if not no_op:
      subprocess.run(s, shell=True, capture_output=True)
    print(f"finished running {s}")
    cv.set()
    job_queue.task_done()
    continue

def run_binning_comparison_single(i, j, tuner_seed, grapher_seed):
  s = f'python3 irace_binning_comparison.py {i} {j} {tuner_seed} {grapher_seed}'
  cv = Event()
  job_queue.put((s, cv))
  cv.wait()

def run_binning_comparison_full(i, tuner_seeds, grapher_seeds):
  tuning_runs = [Thread(target=run_binning_comparison_single, args=(i, j, tuner_seeds[j], grapher_seeds[j])) for j in range(M)]
  for run in tuning_runs:
    run.start()
  for run in tuning_runs:
    run.join()
  s = f'python3 irace_grapher_binning_comparison.py {i} {" ".join(map(str, tuner_seeds))} {" ".join(map(str, grapher_seeds))}'
  cv = Event()
  job_queue.put((s, cv))
  cv.wait()


def run_binning_comparison_with_static_single(i, j, tuner_seed, grapher_seed):
  s = f'python3 irace_binning_comparison_with_static.py {i} {j} {tuner_seed} {grapher_seed}'
  cv = Event()
  job_queue.put((s, cv))
  cv.wait()
  
def run_binning_comparison_with_static_full(i, tuner_seeds, grapher_seeds):
  tuning_runs = [Thread(target=run_binning_comparison_with_static_single, args=(i, j, tuner_seeds[j], grapher_seeds[j])) for j in range(M)]
  for run in tuning_runs:
    run.start()
  for run in tuning_runs:
    run.join()
  s = f'python3 irace_grapher_binning_comparison_with_static.py {i} {" ".join(map(str, tuner_seeds))} {" ".join(map(str, grapher_seeds))}'
  cv = Event()
  job_queue.put((s, cv))
  cv.wait()

def run_baseline_full(i, dynamic_seed, dynamic_bin_seed, static_seed, grapher_seed):
  dynamic_cv = Event()
  job_queue.put((f'python3 irace_dynamic.py {i} {dynamic_seed}', dynamic_cv))
  dynamic_bin_cv = Event()
  job_queue.put((f"python3 irace_dynamic_bin.py {i} {dynamic_bin_seed}", dynamic_bin_cv))
  static_cv = Event()
  job_queue.put((f"python3 irace_static.py {i} {static_seed}", static_cv))
  dynamic_cv.wait()
  dynamic_bin_cv.wait()
  static_cv.wait()

  grapher_cv = Event()
  job_queue.put((f"python3 irace_grapher.py {i} {dynamic_seed} {dynamic_bin_seed} {static_seed} {grapher_seed}", grapher_cv))
  grapher_cv.wait()
  
def run_dynamic_with_static_full(i, seed):
  cv = Event()
  job_queue.put((f'python3 irace_dynamic_with_static.py {i} {seed}', cv))
  cv.wait()

def main(job_type: JobType):
  Thread(target=worker, args=(f"mock-pc", ), daemon=True).start()
  Thread(target=worker, args=(f"mock-pc2", ), daemon=True).start()
  runs = []
  if job_type == JobType.baseline or job_type == JobType.full:
    runs += [Thread(target=run_baseline_full, args=(i, rng.integers(1<<15, (1<<16)-1), rng.integers(1<<15, (1<<16)-1), rng.integers(1<<15, (1<<16)-1), rng.integers(1<<15, (1<<16)-1))) for i in range(N)]
  else: 
    [(i, rng.integers(1<<15, (1<<16)-1), rng.integers(1<<15, (1<<16)-1), rng.integers(1<<15, (1<<16)-1), rng.integers(1<<15, (1<<16)-1)) for i in range(N)]
  seeds = []
  for i in range(N): # Seed batch 1 
    seeds.append((list(rng.integers(1<<15, (1<<16)-1, 11)), list(rng.integers(1<<15, (1<<16)-1, 11))))
  for i in range(N): # Seed batch 2
    one, two = seeds[i]
    if M > 11:
      one += list(rng.integers(1<<15, (1<<16)-1, M - 11))
      two += list(rng.integers(1<<15, (1<<16)-1, M - 11))
    else:
      one = one[:M]
      two = two[:M]
    seeds[i] = (one, two) 
  if job_type == JobType.binning or job_type == JobType.full:
    for i in range(N):
      one, two = seeds[i]
      runs.append(Thread(target=run_binning_comparison_full, args=(i, one, two)))
  if job_type == JobType.binning_with_static or job_type == JobType.full:
    for i in range(N):
      runs.append(Thread(target=run_binning_comparison_with_static_full, args = (i, list(rng.integers(1<<15, (1<<16)-1, M)), list(rng.integers(1<<15, (1<<16)-1, M)))))
  else:
    for i in range(N):
      (i, list(rng.integers(1<<15, (1<<16)-1, M)), list(rng.integers(1<<15, (1<<16)-1, M)))
  if job_type == JobType.dynamic_with_static or job_type == JobType.full:
    runs += [Thread(target=run_dynamic_with_static_full, args=(i, rng.integers(1<<15, (1<<16)-1))) for i in range(N)]
  else:
    [(i, rng.integers(1<<15, (1<<16)-1)) for i in range(N)]
  for thread in runs:
    thread.start()
  for thread in runs:
    thread.join()
  job_queue.join()

if __name__ == '__main__':
  print(sys.argv)
  parser = argparse.ArgumentParser()
  parser.add_argument('job_type', type=JobType, choices=list(JobType), default=JobType.baseline, nargs='?')
  parser.add_argument('--np', default=False, action='store_true')
  args = parser.parse_args()
  no_op = args.np
  main(args.job_type)


