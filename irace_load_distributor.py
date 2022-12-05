from ast import arg
import subprocess
import threading
from threading import Thread
import pathlib
from config import graph, seed, N, M, min_cpu_usage, max_cpu_usage, iterative_seeding_seeds, N2
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
import psutil
import shlex

rng = numpy.random.default_rng(seed)
job_queue = Queue()
no_op = False
current_worker_count = 0
target_worker_count = 0
worker_count_lock = threading.Lock()
worker_serial = 0
has_failed = False
logging.basicConfig(level=logging.INFO, format='%(asctime)s: %(levelname)s: %(message)s',  datefmt="%m/%d/%Y %I:%M:%S %p %Z")

class JobType(Enum):
  baseline = 'baseline'
  binning = 'binning'
  binning_with_static = 'binning_with_static'
  dynamic_with_static = 'dynamic_with_static'
  binning_with_defaults = 'binning_with_defaults'
  binning_with_dynamic = 'binning_with_dynamic'
  binning_no_defaults = 'binning_no_defaults'
  full = 'full'
  def __str__(self):
    return self.value

def worker(name):
  while True:
    logging.info(f"{name} waiting for job")
    s, cv = job_queue.get()
    logging.info(f"{name}: got job: {s}")
    logging.info(f"{name}: running {s}")
    if not no_op:
      p = subprocess.run(s, capture_output=True)
      if p.returncode != 0:
        global has_failed
        logging.error(f"{s} had non zero return code")
        logging.info(f"try {shlex.join(s)}")
        has_failed = True
    logging.info(f"{name}: finished running {s}")
    cv.set()
    job_queue.task_done()
    global current_worker_count, target_worker_count, worker_count_lock
    with worker_count_lock:
      if target_worker_count < current_worker_count:
        logging.info(f"dropping worker {name} because target worker needs to be reduced. After the move, we have {current_worker_count - 1} workers, while aiming for {target_worker_count}")
        current_worker_count -= 1
        return

def run_binning_comparison_single(i, j, tuner_seed, grapher_seed):
  i = str(i)
  j = str(j)
  tuner_seed = str(tuner_seed)
  grapher_seed = str(grapher_seed)
  s = [sys.executable, 'irace_binning_comparison.py', i, j, tuner_seed, grapher_seed]
  cv = Event()
  job_queue.put((s, cv))
  cv.wait()

def run_binning_comparison_full(i, tuner_seeds, grapher_seeds):
  i = str(i)
  tuning_runs = [Thread(target=run_binning_comparison_single, args=(i, j, tuner_seeds[j], grapher_seeds[j])) for j in range(M)]
  for run in tuning_runs:
    run.start()
  for run in tuning_runs:
    run.join()
  s = [sys.executable, 'irace_grapher_binning_comparison.py', i] + list(map(str, tuner_seeds)) + list(map(str, grapher_seeds))
  cv = Event()
  job_queue.put((s, cv))
  cv.wait()


def run_binning_comparison_with_static_single(i, j, tuner_seed, grapher_seed):
  i = str(i)
  j = str(j)
  tuner_seed = str(tuner_seed)
  grapher_seed = str(grapher_seed)
  s = [sys.executable, 'irace_binning_comparison_with_static.py', i, j, tuner_seed, grapher_seed]
  cv = Event()
  job_queue.put((s, cv))
  cv.wait()

def run_binning_comparison_with_static_full(i, tuner_seeds, grapher_seeds):
  i = str(i)
  tuning_runs = [Thread(target=run_binning_comparison_with_static_single, args=(i, j, tuner_seeds[j], grapher_seeds[j])) for j in range(M)]
  for run in tuning_runs:
    run.start()
  for run in tuning_runs:
    run.join()
  s = [sys.executable, 'irace_grapher_binning_comparison_with_static.py', i] + list(map(str, tuner_seeds)) + list(map(str, grapher_seeds))
  cv = Event()
  job_queue.put((s, cv))
  cv.wait()

def run_baseline_full(i, dynamic_seed, dynamic_bin_seed, static_seed, grapher_seed):
  i = str(i)
  dynamic_seed = str(dynamic_bin_seed)
  dynamic_bin_seed = str(dynamic_bin_seed)
  static_seed = str(static_seed)
  grapher_seed = str(grapher_seed)
  dynamic_cv = Event()
  job_queue.put(([sys.executable, 'irace_dynamic.py', i, dynamic_seed], dynamic_cv))
  dynamic_bin_cv = Event()
  job_queue.put(([sys.executable, 'irace_dynamic_bin.py', i, dynamic_bin_seed], dynamic_bin_cv))
  static_cv = Event()
  job_queue.put(([sys.executable, 'irace_static.py', i, static_seed], static_cv))
  dynamic_cv.wait()
  dynamic_bin_cv.wait()
  static_cv.wait()

  grapher_cv = Event()
  job_queue.put(([sys.executable, 'irace_grapher.py', i, dynamic_seed, dynamic_bin_seed, static_seed, grapher_seed], grapher_cv))
  grapher_cv.wait()
  
def run_dynamic_with_static_full(i, tuner_seed, grapher_seed):
  i = str(i)
  tuner_seed = str(tuner_seed)
  grapher_seed = str(grapher_seed)
  cv = Event()
  job_queue.put(([sys.executable, 'irace_dynamic_with_static.py', i, tuner_seed, grapher_seed], cv))
  cv.wait()

def run_binning_with_defaults(i, tuner_seeds, grapher_seeds):
  i = str(i)
  cv = Event()
  job_queue.put(([sys.executable, 'irace_binning_with_defaults.py', i], cv))
  cv.wait()

def run_binning_no_defaults(i, tuner_seeds, grapher_seeds):
  i = str(i)
  cv = Event()
  job_queue.put(([sys.executable, 'irace_binning_no_defaults.py', i], cv))
  cv.wait()

def run_binning_with_dynamic(i):
  i = str(i)
  cv = Event()
  job_queue.put(([sys.executable, 'eval_binning_with_dynamic.py', i], cv))
  cv.wait()

def worker_adjustment():
  global target_worker_count, current_worker_count, worker_serial, worker_count_lock
  while True:
    time.sleep(20)
    cpu_usage = psutil.cpu_percent() / 100
    if cpu_usage < min_cpu_usage and job_queue.qsize() != 0:
      with worker_count_lock:
        target_worker_count = current_worker_count + 1
        logging.info(f"increase worker count to {current_worker_count + 1}")
        Thread(target=worker, args=(f"mock-pc{worker_serial}", ), daemon=True).start()
        current_worker_count += 1
        worker_serial += 1
    elif cpu_usage > max_cpu_usage and target_worker_count > 1:
      with worker_count_lock:
        if target_worker_count != current_worker_count - 1:
          logging.info(f"down adjusting target workder count {current_worker_count - 1}")
        target_worker_count = current_worker_count - 1
      

def main(job_type: JobType):
  for i in range(2):
    global target_worker_count, current_worker_count, worker_serial
    Thread(target=worker, args=(f"mock-pc{i}", ), daemon=True).start()
    target_worker_count = 2
    current_worker_count = 2
    worker_serial = 2
  Thread(target=worker_adjustment, args=(), daemon=True).start()
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
    runs += [Thread(target=run_dynamic_with_static_full, args=(i, rng.integers(1<<15, (1<<16)-1), rng.integers(1<<15, (1<<16)-1))) for i in range(N)]
  else:
    [(i, rng.integers(1<<15, (1<<16)-1), rng.integers(1<<15, (1<<16)-1)) for i in range(N)]
  if job_type == JobType.binning_with_defaults or job_type == JobType.full:
    runs += [Thread(target=run_binning_with_defaults, args=(i, iterative_seeding_seeds[i][0], iterative_seeding_seeds[i][1])) for i in range(N2)]
  if job_type == JobType.binning_no_defaults or job_type == JobType.full:
    runs += [Thread(target=run_binning_no_defaults, args=(i, iterative_seeding_seeds[i][0], iterative_seeding_seeds[i][1])) for i in range(N2)]
  if job_type == JobType.binning_with_dynamic or job_type == JobType.full:
    runs += [Thread(target=run_binning_with_dynamic, args=(i,)) for i in range(N2)]
  for thread in runs:
    thread.start()
  for thread in runs:
    thread.join()
  job_queue.join()
  if has_failed:
    return 1
  else:
    return 0

if __name__ == '__main__':
  logging.info(sys.argv)
  parser = argparse.ArgumentParser()
  parser.add_argument('job_type', type=JobType, choices=list(JobType), default=JobType.baseline, nargs='?')
  parser.add_argument('--np', default=False, action='store_true')
  args = parser.parse_args()
  no_op = args.np
  exit(main(args.job_type))


