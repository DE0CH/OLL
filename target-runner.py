from numpy import argsort
import sys
from onell_algs import onell_lambda

seed = int(sys.argv[3])
instance = sys.argv[4]
with open(instance) as f:
    n = int(f.read())

lbds = [1] * n
for i in range(n):
    j = int(sys.argv[i*2+5].replace("--lbd", ""))
    lbd = int(sys.argv[i*2+6])
    lbds[j] = lbd

a, b, c = onell_lambda(n, lbds=lbds, seed=seed)
print(c)