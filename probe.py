import argparse
import pathlib
import os

parser = argparse.ArgumentParser()
parser.add_argument("n")
args = parser.parse_args()

pathlib.Path("test").mkdir(exist_ok=True, parents=True)
with open(f"test/{args.n}.txt", 'w') as f:
    f.write(args.n + '\n')
    f.write(str(os.cpu_count()))
