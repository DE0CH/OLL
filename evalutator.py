#! /usr/bin/env python3

from onell_algs import onell_lambda, onell_dynamic_theory, onell_dynamic_5params
import numpy as np
import random

n = 100
seed = 1511431338 
true_random = True
if true_random:
    rng: np.random.Generator = np.random.default_rng(random.randint(10**10, 10**11))
else:
    rng: np.random.Generator = np.random.default_rng(1511431338)
def next_seed():
     rng.integers(low=10**10, high=10**11)
random_lbd = list(rng.integers(low=1, high=n, size=n))
dynamic_lbd = None

with open('lbd_dynamic_optimal.txt') as f:
    for line in f:
        if line.strip():
            dynamic_lbd = list(map(int, line.split()))[1:]
            break
assert dynamic_lbd is not None
static_lbd = [5]*n

def main():
    # print("Dynamic Lambda")
    # print(onell_lambda(n, lbds=dynamic_lbd, seed=next_seed()))
    print("Static Lambda")
    print(onell_lambda(n, lbds=static_lbd, seed=next_seed()))
    print("Random Lambda")
    print(onell_lambda(n, lbds=random_lbd, seed=next_seed()))
    print("Lambda = 1")
    print(onell_lambda(n, lbds=[1]*n, seed=next_seed()))
    print("Dynamic Theory")
    print(onell_dynamic_theory(n, seed=next_seed()))
    print("5 Parameters")
    print(onell_dynamic_5params(n, seed=next_seed()))

    


if __name__ == "__main__":
    main()