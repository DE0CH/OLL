#!/usr/bin/env python3 

import sys
from onell_algs import onell_lambda
from config import get_bins, suppress_stderr

seed = int(sys.argv[3])
instance = sys.argv[4]
bound = float(sys.argv[5])
with open(instance) as f:
  n = int(f.read())

bins, bin_lookup = get_bins(n)

lbds = [1] * n
lbd_bins = [1] * len(bins)
for i in range(len(bins)):
  j = int(sys.argv[i*2+6].replace("--lbd", ""))
  lbd = float(sys.argv[i*2+7])
  lbd_bins[j] = lbd

for i in range(n):
  lbds[i] = lbd_bins[bin_lookup[i]]

with suppress_stderr():
  a, b, c = onell_lambda(n, lbds=lbds, max_evals=bound, seed=seed)
print(c)
print(c)