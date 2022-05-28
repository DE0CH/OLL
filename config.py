import multiprocessing
import os
from dotenv import load_dotenv

load_dotenv()

SMALL = os.getenv("SMALL", None)
EMAIL = os.getenv("EMAIL", "false").strip() == "true"

if SMALL == "small":
  N = 3
elif SMALL == "xsmall":
  N = 2
else:
  N = 6

trials = 500 
threads = int(multiprocessing.cpu_count() * 1.5)
smac_instances = 26
seed = 16950281577708742744
seed_small = 2213319694

sizes = [
  10, 
  50, 
  100,
  200, 
  500,
  1000
]

if SMALL == "small":
  experiment_multiples_dynamic = [
    50, 
    30, 
    20, 
    10,
    10,
    10
  ]
elif SMALL == "xsmall":
  experiment_multiples_dynamic = [
    10, 
    10,
  ]
else:
  experiment_multiples_dynamic = [
    10**5, 
    10**5,
    10**5,
    50000,
    20000,
    10000,
  ] 

if SMALL=="small":
  experiment_multiples_static = [50, 30, 20, 10, 10, 10]
elif SMALL=="xsmall":
  experiment_multiples_static = [1, 1]
else: 
  experiment_multiples_static = [100] * N