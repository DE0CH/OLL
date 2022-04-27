#! /usr/bin/env python3

from onell_algs import onell_lambda, onell_dynamic_theory, onell_dynamic_5params
import numpy as np

n = 1000
seed = 1511431338 
rng = np.random.default_rng(1511431338)
random_lbd = rng.integers(low=1, high=n, size=n)
dynamic_lbd = None
with open('lbd_dynamic_optimal.txt') as f:
    for line in f:
        if line.strip():
            dynamic_lbd = list(map(int, line.split()))[1:]
            break
assert dynamic_lbd is not None
static_lbd = [90]*n

def main():
    print("Dynamic Lambda")
    print(onell_lambda(lbd=dynamic_lbd, seed=))
    print("Static Lambda")
    print("Random Lambda")
    print(onell_lambda(random_lbd))
    print("Lambda = 1")
    print("Dynamic Theory")
    print(onell_dynamic_theory(n))
    print("5 Parameters")
    


if __name__ == "__main__":
    main()