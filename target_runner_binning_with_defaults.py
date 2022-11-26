#!/usr/bin/env python3 

import sys
from onell_algs_rs import onell_lambda
from config import iterative_seeding_multiples, iterative_seeding_sizes, suppress_stderr, get_iter_bins, flatten_lbds, c_string, d_string

seed = int(sys.argv[3])
instance = sys.argv[4]
bound = int(float(sys.argv[5]))
with open(instance) as f: 
  n, i = f.read().split()
  n = int(n)
  i = int(i[1:]) # Because of my stupid code structure (blame oop for this), this number starts with _

bin_count = i + 1

lbd_bins = [1] * bin_count
for i in range(bin_count):
  j = int(sys.argv[i*2+6].replace("--lbd", ""))
  lbd = float(sys.argv[i*2+7])
  lbd_bins[j] = lbd

lbds = flatten_lbds(lbd_bins, get_iter_bins(n, bin_count))

with suppress_stderr():
  c = onell_lambda(n, lbds, seed, bound)
print(c_string(c))
print(d_string(c))
