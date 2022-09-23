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

rng = numpy.random.default_rng(seed)
mock = False
job_queue = Queue()

class JobType(Enum):
  baseline = 'baseline'
  binning = 'binning'
  full = 'full'
  def __str__(self):
    return self.value

def worker(name):
  while True:
    print(f"{name} waiting for job")
    if mock:
      s, cv = job_queue.get()
      print(f"got job: {s}")
      print(f"running {s}")
      subprocess.run(s, shell=True, capture_output=True)
      cv.set()
      job_queue.task_done()
      continue

    tmp_dir_name = f"/home/dc262/.posco/{str(uuid4())}"

    pathlib.Path("logs").mkdir(parents=True, exist_ok=True)

    print(f"Testing if {name}, is on:")
    message = subprocess.run(['ssh', '-o', 'ConnectTimeout=20', name, 'uname'], capture_output=True).stderr.decode('utf-8')
    print(f"Finished testing on {name}")
    success = not (message.startswith("ssh: connect to host") or message.startswith('ssh: Could not resolve'))
    if not success:
      print(f"connection to {name} timed out, dropping the worker")
      return
    else:
      s, cv = job_queue.get()
      return_codes = []
      s = f'docker build -t irace . && docker run --rm {("--env SMALL="+os.getenv("SMALL") + " ") if os.getenv("SMALL") else ""}-v {tmp_dir_name}:/usr/app irace ' + s
      print(f"{name} is indeed on")
      try:
        return_codes.append(subprocess.run(['ssh', name, f'mkdir -p {os.path.dirname(tmp_dir_name)}']).returncode)
        return_codes.append(subprocess.run(['rsync', '-azvPI', '--delete', f"{os.getcwd()}/", f'{name}:{tmp_dir_name}'], stdout=subprocess.DEVNULL).returncode)
        with open(f"logs/{name}_stdout.log", "wb") as stdoutf:
          with open(f"logs/{name}_stderr.log", "wb") as stderrf:
            print(f"Running {s} on {name}")
            return_codes.append(subprocess.run(['ssh', name, f"cd {tmp_dir_name} && " + s], stdout=stdoutf, stderr=stderrf).returncode)
            print(f"Finished running on {name}") 
        return_codes.append(subprocess.run(['rsync', '-azvP', f'{name}:{tmp_dir_name}/', '.'], stdout=subprocess.DEVNULL).returncode)
        rerun = functools.reduce(lambda x, y: x | y, return_codes) != 0
      except:
        logging.exception("except occured, retrying")
        rerun = True
      if rerun:
        print(f"putting {s} back into the queue because it has failed")
        job_queue.put((s, cv))
        job_queue.task_done()
      else:
        print(f"{s} completed successfully on {name}")
        cv.set()
        job_queue.task_done()

def run_binning_comparison_single(i, j, tuner_seed, grapher_seed):
  if i < N-1:
    return
  s = f'python3 irace_binning_comparison.py {i} {j} {tuner_seed} {grapher_seed}'
  cv = Event()
  job_queue.put((s, cv))
  cv.wait()

def run_binning_comparison_full(i, tuner_seeds, grapher_seeds):
  if i < N-1:
    return
  tuning_runs = [Thread(target=run_binning_comparison_single, args=(i, j, tuner_seeds[j], grapher_seeds[j])) for j in range(M)]
  for run in tuning_runs:
    run.start()
  for run in tuning_runs:
    run.join()
  s = f'python3 irace_grapher_binning_comparison.py {i} {" ".join(map(str, tuner_seeds))} {" ".join(map(str, grapher_seeds))}'
  cv = Event()
  job_queue.put((s, cv))
  cv.wait()


def run_baseline_full(i, dynamic_seed, dynamic_bin_seed, static_seed, grapher_seed):
  if i < N - 2:
    return
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
  
def main(job_type: JobType):
  if mock:
    Thread(target=worker, args=(f"mock-pc", ), daemon=True).start()
    Thread(target=worker, args=(f"mock-pc2", ), daemon=True).start()
  else:
    for i in range(1, 80):
      Thread(target=worker, args=(f"pc8-{i:03d}-l", ), daemon=True).start()
  runs = []
  if job_type == JobType.baseline or job_type == JobType.full:
    runs += [Thread(target=run_baseline_full, args=(i, rng.integers(1<<15, (1<<16)-1), rng.integers(1<<15, (1<<16)-1), rng.integers(1<<15, (1<<16)-1), rng.integers(1<<15, (1<<16)-1))) for i in range(N)]
  if job_type == JobType.binning or job_type == JobType.full:
    for i in range(N):
      runs.append(Thread(target=run_binning_comparison_full, args=(i, list(rng.integers(1<<15, (1<<16)-1, M)), list(rng.integers(1<<15, (1<<16)-1, M)))))
  for thread in runs:
    thread.start()
  for thread in runs:
    thread.join()
  job_queue.join()

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('job_type', type=JobType, choices=list(JobType), default=JobType.baseline, nargs='?')
  parser.add_argument('--mock', action="store_true")
  args = parser.parse_args()
  mock = args.mock

  main(args.job_type)


