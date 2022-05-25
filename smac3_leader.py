import subprocess 
import config 
import threading
import multiprocessing.pool 
import multiprocessing
import dotenv
import os
import logging 

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
dotenv.load_dotenv()


def run(i, machine):
  dir_path = os.path.dirname(__file__)
  while True:
    with machine.get_lock():
      n = machine.value
      machine.value -= 1
    pc_name = f'pc8-{n:03}-l'
    try:
      logging.info(f"trying to run i = {i} on machine {pc_name}")
      subprocess.run(['rsync', '-azPI', '--delete', '--timeout=60', dir_path, f"{pc_name}:{dir_path}"], capture_output=True).check_returncode()
      subprocess.run(['ssh', '-o', 'ConnectTimeout=60', f'SMALL={config.SMALL}', pc_name, os.path.join(dir_path, 'smac3_launcher.py')], f'{i}').check_returncode()
      subprocess.run(['rsync', '-azP', '--timeout=60', f"{pc_name}:{os.path.join(dir_path, 'smac_output')}/"])
    except subprocess.CalledProcessError:
      logging.info(f"machine {pc_name} for i = {i} timeout, trying the next one")

if __name__ == '__main__':
  logging.info("starting")
  tpool = multiprocessing.pool.ThreadPool()
  machine = multiprocessing.Value('i', 79)
  for i in range(config.N):
    tpool.apply_async(run, args=(i, machine))
  tpool.close()
  tpool.join()

