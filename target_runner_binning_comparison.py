#!/usr/bin/env python3 

import sys
from onell_algs import onell_lambda
from config import get_bins, descent_rates

seed = int(sys.argv[3])
instance = sys.argv[4]
bound = int(sys.argv[5])
with open(instance) as f:
  n, descent_rate_j = map(int, f.read().split())
  descent_rate = descent_rates[descent_rate_j]

bins, bin_lookup = get_bins(n, descent_rate=descent_rate)

lbds = [1] * n
lbd_bins = [1] * len(bins)
for i in range(len(bins)):
  j = int(sys.argv[i*2+6].replace("--lbd", ""))
  lbd = int(sys.argv[i*2+7])
  lbd_bins[j] = lbd

for i in range(n):
  lbds[i] = lbd_bins[bin_lookup[i]]

a, b, c = onell_lambda(n, lbds=lbds, max_evals=bound, seed=seed)
print(c)
print(c)
