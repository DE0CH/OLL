import subprocess 
import config 
import threading
import multiprocessing.pool 
import multiprocessing
import dotenv
import os
import logging 
import send_email
import socket


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
      subprocess.run(['rsync', '-azPI', '--delete', '--timeout=10', f"{dir_path}/", f"{pc_name}:{dir_path}"]).check_returncode()
      subprocess.run(['ssh', '-o', 'ConnectTimeout=10', pc_name, f'SMALL={config.SMALL}', os.path.join(dir_path, 'smac-launcher-conda.sh'), f'{i}']).check_returncode()
      subprocess.run(['rsync', '-azP', '--timeout=10', f"{pc_name}:{os.path.join(dir_path, 'smac_output')}/", os.path.join(dir_path, 'smac_output')]).check_returncode()
      if config.EMAIL:
        send_email.main(f"{socket.gethostname()}: irace done with i = {i} size = {config.sizes[i]}")
      break
    except subprocess.CalledProcessError:
      logging.info(f"machine {pc_name} for i = {i} timeout, trying the next one")

if __name__ == '__main__':
  logging.info("starting")
  tpool = multiprocessing.pool.ThreadPool()
  machine = multiprocessing.Value('i', 70)
  for i in range(config.N):
    tpool.apply_async(run, args=(i, machine))
  tpool.close()
  tpool.join()

