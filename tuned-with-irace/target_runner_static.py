#! /usr/bin/env python3

import sys
from onell_algs_rs import onell_lambda
from config import suppress_stderr, c_string, d_string

seed = int(sys.argv[3])
instance = sys.argv[4]
bound = int(float(sys.argv[5]))
with open(instance) as f:
    n = int(f.read())


lbd = float(sys.argv[7])
lbds = [lbd]*n

with suppress_stderr():
  c = onell_lambda(n, lbds, seed, bound)
print(c_string(c, n, bound))
print(d_string(c, n, bound))