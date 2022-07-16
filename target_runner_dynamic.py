#!/usr/bin/env python3 

import sys
from onell_algs import onell_lambda

seed = int(sys.argv[3])
instance = sys.argv[4]
bound = int(sys.argv[5])
with open(instance) as f:
    n = int(f.read())

lbds = [1] * n
for i in range(n):
    j = int(sys.argv[i*2+6].replace("--lbd", ""))
    lbd = float(sys.argv[i*2+7])
    lbds[j] = lbd

a, b, c = onell_lambda(n, lbds=lbds, max_evals=bound, seed=seed)
print(c)
print(c)