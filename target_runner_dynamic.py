#!/usr/bin/env python3 

import sys
from typing import SupportsRound
from onell_algs_rs import onell_lambda
from config import suppress_stderr, c_string, d_string

seed = int(sys.argv[3])
instance = sys.argv[4]
bound = int(float(sys.argv[5]))
with open(instance) as f:
    n = int(f.read())

lbds = [1] * n
for i in range(n):
    j = int(sys.argv[i*2+6].replace("--lbd", ""))
    lbd = float(sys.argv[i*2+7])
    lbds[j] = lbd

with suppress_stderr():
  c = onell_lambda(n, lbds, seed, bound)
print(c_string(c))
print(d_string(c))