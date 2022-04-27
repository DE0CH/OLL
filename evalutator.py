#! /usr/bin/env python3

from onell_algs import onell_lambda, onell_dynamic_theory, onell_dynamic_5params
import numpy as np
import random
import matplotlib.pyplot as plt
from multiprocessing import Pool

n = 100
seed = 1511431338 
true_random = False
if true_random:
    rng: np.random.Generator = np.random.default_rng(random.randint(10**10, 10**11))
else:
    rng: np.random.Generator = np.random.default_rng(1511431338)
def next_seed():
    return rng.integers(low=10**10, high=10**11)
def next_seeds(size):
    res = list(rng.integers(low=10**10, high=10**11, size=size))
    return res
random_lbd = list(rng.integers(low=1, high=n, size=n))
dynamic_lbd = None
trials = 500
threads = 24
random_lbd_set = [list(rng.integers(low=1, high=n, size=n)) for _ in range(trials)]
with open('dynamic_lbd_optimal.txt') as f:
    dynamic_lbd = list(map(int, f.read().split()))

assert dynamic_lbd is not None
static_lbd = [5]*n

def onell_eval(f, n, lbds, seed):
    if lbds:
        res = f(n, lbds=lbds, seed=seed)
    else:
        res = f(n, seed=seed)
    if res[1] != n:
        print(f"Capped with {f}, {n}, {lbds}, {seed}")
    return res[2]


def main():
    with Pool(threads) as p:
        static_lbd_performace = p.starmap(onell_eval, zip([onell_lambda]*trials, [n]*trials, [static_lbd]*trials, next_seeds(trials)))
        dynamic_lbd_performace = p.starmap(onell_eval, zip([onell_lambda]*trials, [n]*trials, [dynamic_lbd]*trials, next_seeds(trials)))
        random_lbd_performace = p.starmap(onell_eval, zip([onell_lambda]*trials, [n]*trials, random_lbd_set, next_seeds(trials)))
        random_lbd_same_performace = p.starmap(onell_eval, zip([onell_lambda]*trials, [n]*trials, [random_lbd]*trials, next_seeds(trials)))
        one_lbd_performace = p.starmap(onell_eval, zip([onell_lambda]*trials, [n]*trials, [[1]*n]*trials, next_seeds(trials)))
        dynamic_theory_performace = p.starmap(onell_eval, zip([onell_dynamic_theory]*trials, [n]*trials, [None]*trials, next_seeds(trials)))
        five_param_performace = p.starmap(onell_eval, zip([onell_dynamic_5params]*trials, [n]*trials, [None]*trials, next_seeds(trials)))
    plt.boxplot((static_lbd_performace, dynamic_lbd_performace, random_lbd_performace, random_lbd_same_performace, one_lbd_performace, dynamic_theory_performace, five_param_performace), labels=(f"Static Lambda (lbd={5})", "Dynamic Lambda", "Random Lambda (Lambda changes)", "Random Lambda (Lambda fixed)", "Lambda = 1", "Dynamic Theory", "Five Parameters"))
    plt.show()
    return 
    # print("Dynamic Lambda")
    # print(onell_lambda(n, lbds=dynamic_lbd, seed=next_seed()))
    print("Static Lambda")
    print(sum([onell_lambda(n, lbds=static_lbd, seed=next_seed())[2] for i in range(trials)]) / trials)
    print("Random Lambda")
    print(sum([onell_lambda(n, lbds=random_lbd, seed=next_seed())[2] for i in range(trials)]) / trials)
    print("Lambda = 1")
    print(sum([onell_lambda(n, lbds=[1]*n, seed=next_seed())[2] for i in range(trials)]) / trials)
    print("Dynamic Theory")
    print(sum([onell_dynamic_theory(n, seed=next_seed())[2] for i in range(trials)]) / trials)
    print("5 Parameters")
    print(sum([onell_dynamic_5params(n, seed=next_seed())[2] for i in range(trials)]) / trials)

    


if __name__ == "__main__":
    main()