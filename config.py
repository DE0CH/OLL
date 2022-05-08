SMALL = False
N = 3

trials = 500 
threads = 15
seed = 16950281577708742744

sizes = [
  10, 
  50, 
  100,
]

if not SMALL:
  experiment_multiples_dynamic = [10**4] * N
else:
  experiment_multiples_dynamic = [50, 30, 20]

if not SMALL:
  experiment_multiples_static = [100] * N
else:
  experiment_multiples_static = [50, 30, 20]
