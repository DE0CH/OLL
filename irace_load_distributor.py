import subprocess
import threading
from threading import Thread
import pathlib
from config import seed, N, M
import numpy
import argparse
import os
from enum import Enum 

current_computer = 1
lock = threading.Lock()
rng = numpy.random.default_rng(seed)
mock_docker = False 
mock = False

class JobType(Enum):
  baseline = 'baseline'
  binning = 'binning'
  def __str__(self):
    return self.value

def run_job(s):
  if mock:
    print(f"running {s}")
    subprocess.run(s, shell=True, capture_output=True)
    return

  s = f'docker build -t irace . && docker run --rm {("--env SMALL="+os.getenv("SMALL") + " ") if os.getenv("SMALL") else ""}-v {"/home/dc262/OLL" if not mock_docker else os.getcwd()}:/usr/app irace ' + s
  if mock_docker:
    print(f"running {s}")
    subprocess.run(s, shell=True, capture_output=True)
    return
  # This is very ad hoc, not a general and reusable function at all, but too lazy to fix it
  success = False 
  global current_computer
  while not success:
    with lock:
      i = current_computer
      if current_computer < 79:
        current_computer += 1
      else:
        current_computer = 1
    name = f"pc8-{i:03d}-l"
    pathlib.Path("logs").mkdir(parents=True, exist_ok=True)

    print(f"Testing if {name}, is on:")
    message = subprocess.run(['ssh', '-o', 'ConnectTimeout=20', name, 'uname'], capture_output=True).stderr.decode('utf-8')
    print(f"Finished testing on {name}")
    success = not (message.startswith("ssh: connect to host") or message.startswith('ssh: Could not resolve'))
    if not success:
      print(f"connection to {name} timed out, retrying the next machine")
    else:
      subprocess.run(['rsync', '-azvPI', '--delete', '/home/dc262/OLL/', f'{name}:/home/dc262/OLL'], stdout=subprocess.DEVNULL)
      with open(f"logs/{name}_stdout.log", "wb") as stdoutf:
        with open(f"logs/{name}_stderr.log", "wb") as stderrf:
          print(f"Running {s} on {name}")
          subprocess.run(['ssh', name, "cd /home/dc262/OLL && " + s], stdout=stdoutf, stderr=stderrf)
          print(f"Finished running on {name}") 
      subprocess.run(['rsync', '-azvP', f'{name}:/home/dc262/OLL/', '.'], stdout=subprocess.DEVNULL)

def run_binning_comparison_single(i, j, tuner_seed, grapher_seed):
  tuning_run = Thread(target=run_job, args=(f'python3 irace_binning_comparison.py {i} {j} {tuner_seed} {grapher_seed}',))
  tuning_run.start()
  tuning_run.join()

def run_binning_comparison_full(i, tuner_seeds, grapher_seeds):
  tuning_runs = [Thread(target=run_binning_comparison_single, args=(i, j, tuner_seeds[j], grapher_seeds[j])) for j in range(M)]
  for run in tuning_runs:
    run.start()
  for run in tuning_runs:
    run.join()
  
  grapher_run = Thread(target=run_job, args=(f'python3 irace_grapher_binning_comparison.py {i} {" ".join(map(str, tuner_seeds))} {" ".join(map(str, grapher_seeds))}', ))
  grapher_run.start()
  grapher_run.join()


def run_baseline_full(i, dynamic_seed, dynamic_bin_seed, static_seed, grapher_seed):
  dynamic_run = Thread(target=run_job, args=(f'python3 irace_dynamic.py {i} {dynamic_seed}',))
  dynamic_bin_run = Thread(target=run_job, args=(f"python3 irace_dynamic_bin.py {i} {dynamic_bin_seed}",))
  static_run = Thread(target=run_job, args=(f"python3 irace_static.py {i} {static_seed}",))
  grapher_run = Thread(target=run_job, args=(f"python3 irace_grapher.py {i} {dynamic_seed} {dynamic_bin_seed} {static_seed} {grapher_seed}", ))
  dynamic_run.start()
  dynamic_bin_run.start()
  static_run.start()
  dynamic_run.join()
  dynamic_bin_run.join()
  static_run.join()
  grapher_run.start()
  grapher_run.join()
  
def main(job_type: JobType):
  if job_type == JobType.baseline:
    runs = [Thread(target=run_baseline_full, args=(i, rng.integers(1<<15, (1<<16)-1), rng.integers(1<<15, (1<<16)-1), rng.integers(1<<15, (1<<16)-1), rng.integers(1<<15, (1<<16)-1))) for i in range(N)]
  elif job_type == JobType.binning:
    runs = []
    for i in range(N):
      runs.append(Thread(target=run_binning_comparison_full, args=(i, list(rng.integers(1<<15, (1<<16)-1, M)), list(rng.integers(1<<15, (1<<16)-1, M)))))
  for thread in runs:
    thread.start()
  for thread in runs:
    thread.join()

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('job_type', type=JobType, choices=list(JobType), default=JobType.baseline, nargs='?')
  parser.add_argument('--mock-docker', action="store_true")
  parser.add_argument('--mock', action="store_true")
  args = parser.parse_args()
  mock_docker = args.mock_docker
  mock = args.mock

  main(args.job_type)


