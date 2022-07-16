#! /usr/bin/env python3

import sys
from onell_algs import onell_lambda
from config import suppress_stderr

seed = int(sys.argv[3])
instance = sys.argv[4]
bound = float(sys.argv[5])
with open(instance) as f:
    n = int(f.read())


lbd = float(sys.argv[7])
lbds = [lbd]*n

with suppress_stderr():
    a, b, c = onell_lambda(n, lbds=lbds, max_evals=bound, seed=seed)
print(c)
print(c)