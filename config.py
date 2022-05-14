import multiprocessing
import os

SMALL = os.getenv("SMALL", None)

if SMALL == "small":
  N = 3
elif SMALL == "xsmall":
  N = 1
else:
  N = 6

trials = 500 
threads = int(multiprocessing.cpu_count() * 1.5)
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
  ]
else:
  experiment_multiples_dynamic = [
    10**4, 
    10**4,
    10**4,
    5000,
    2000,
    1000,
  ] 

if SMALL=="small":
  experiment_multiples_static = [50, 30, 20, 10, 10, 10]
elif SMALL=="xsmall":
  experiment_multiples_static = [1]
else: 
  experiment_multiples_static = [100] * N