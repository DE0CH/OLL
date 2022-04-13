from numpy import argsort
#! /usr/local/bin/python3

from onell_algs import onell_lambda, onell_dynamic_5params
import argparse

parser = argparse.ArgumentParser("Designed for irace")
parser.add_argument("configuration_id")
parser.add_argument("instance_id")
parser.add_argument("seed", type=int)
parser.add_argument("instance", type=str)
parser.add_argument("-A", type=float)
parser.add_argument("-b", type=float)

args = parser.parse_args()
with open(args.instance) as f:
    n = int(f.read())

a, b, c = onell_dynamic_5params(n, seed=args.seed, alpha=1, beta=1, gamma=1, A=args.A, b=args.b)
print(c)