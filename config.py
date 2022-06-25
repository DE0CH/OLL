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
smac_instances = 36
seed = 16950281577708742744
seed_small = 2213319694
descend_rate = 1.5
first_bin_portion = 1-(1/descend_rate)

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
    5*10**3, 
    10**3,
    5*10**2,
    250,
    100,
    50,
  ] 

if SMALL=="small":
  experiment_multiples_static = [50, 30, 20, 10, 10, 10]
elif SMALL=="xsmall":
  experiment_multiples_static = [1, 1]
else: 
  experiment_multiples_static = [100] * N