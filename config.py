import multiprocessing

SMALL = False
N = 6

trials = 500 
threads = int(multiprocessing.cpu_count() * 1.5)
seed = 16950281577708742744

sizes = [
  10, 
  50, 
  100,
  200, 
  500,
  1000
]

if not SMALL:
  experiment_multiples_dynamic = [
    10**4, 
    10**4,
    10**4,
    5000,
    2000,
    1000,
  ] 
else:
  experiment_multiples_dynamic = [
    50, 
    30, 
    20, 
    10,
    10,
    10
  ]

if not SMALL:
  experiment_multiples_static = [100] * N
else:
  experiment_multiples_static = [50, 30, 20, 10, 10, 10]
