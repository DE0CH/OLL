#! /usr/bin/env python3

import sys
from onell_algs import onell_lambda

seed = int(sys.argv[3])
instance = sys.argv[4]
with open(instance) as f:
    n = int(f.read())

for i in range(1):
    lbd = int(sys.argv[i*2+6])
    lbds = [lbd]*n

a, b, c = onell_lambda(n, lbds=lbds, seed=seed)
print(c)