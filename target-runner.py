from numpy import argsort
#! /usr/local/bin/python3

from onell_algs import onell_lambda
import argparse

parser = argparse.ArgumentParser("Designed for irace")
parser.add_argument("configuration_id")
parser.add_argument("instance_id")
parser.add_argument("seed", type=int)
parser.add_argument("instance", type=str)
parser.add_argument("--lbd", type=int)
args = parser.parse_args()
with open(args.instance) as f:
    n = int(f.read())

a, b, c = onell_lambda(n, lbd = args.lbd, max_evals=1000)
print(c)