import multiprocessing
import os

N = 6

seed = 16950281577708742744
sizes = [
  10, 
  50, 
  100,
  200, 
  500,
  1000
]

experiment_multiples_dynamic = [
  10**4, 
  10**4,
  10**4,
  5000,
  2000,
  1000,
] 

experiment_multiples_static = [100] * N