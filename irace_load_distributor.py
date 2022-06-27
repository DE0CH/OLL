import subprocess
import threading
from threading import Thread
import pathlib
from config import seed, N
import numpy
import argparse
import os

current_computer = 1
lock = threading.Lock()
rng = numpy.random.default_rng(seed)
mock = False 

def run_job(s):
  s = f'docker build -t irace . && docker run --rm -it {"--env SMALL="+os.getenv("SMALL") + " " if os.getenv("SMALL") else ""}-v $HOME/OLL:/usr/app irace ' + s
  if mock:
    print(f"running {s}")
    subprocess.run(s, shell=True, capture_output=True)
    return
  # This is very ad hoc, not a general and reusable function at all, but too lazy to fix it
  success = False 
  global current_computer
  while not success:
    with lock:
      i = current_computer
      current_computer += 1
    name = f"pc8-{i:03d}-l"
    pathlib.Path("logs").mkdir(parents=True, exist_ok=True)

    print(f"Testing if {name}, is on:")
    message = subprocess.run(['ssh', '-o', 'ConnectTimeout=20', name, 'uname'], capture_output=True).stderr.decode('utf-8')
    print(f"Finished testing on {name}")
    success = not (message.startswith("ssh: connect to host") or message.startswith('ssh: Could not resolve'))
    if not success:
      print(f"connection to {name} timed out, retrying the next machine")
    else:
      subprocess.run(['rsync', '-azvPI', '--delete', './', f'{name}:$HOME/OLL'], stdout=subprocess.DEVNULL)
      with open(f"logs/{name}_stdout.log", "wb") as stdoutf:
        with open(f"logs/{name}_stderr.log", "wb") as stderrf:
          print(f"Running {s} on {name}")
          subprocess.run(['ssh', name, s], stdout=stdoutf, stderr=stderrf)
          print(f"Finished running on {name}") 
      subprocess.run(['rsync', '-azvP', f'{name}:$HOME/OLL/', '.'], stdout=subprocess.DEVNULL)
      
def run_full(i, dynamic_seed, dynamic_bin_seed, static_seed, grapher_seed):
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
  
def main():
  runs = [Thread(target=run_full, args=(i, rng.integers(1<<15, (1<<16)-1), rng.integers(1<<15, (1<<16)-1), rng.integers(1<<15, (1<<16)-1), rng.integers(1<<15, (1<<16)-1))) for i in range(N)]
  for thread in runs:
    thread.start()
  for thread in runs:
    thread.join()

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('--mock', action="store_true")
  args = parser.parse_args()
  mock = args.mock
  main()


