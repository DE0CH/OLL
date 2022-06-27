from irace_launcher import IraceCallerStatic
import argparse
from config import sizes, experiment_multiples_static
import json

def main(i, seed):
  caller = IraceCallerStatic(sizes[i], experiment_multiples_static[i], seed)
  caller.run()
  with open(f"irace_output/best_config_static_{sizes[i]}_{experiment_multiples_static[i]}_{seed}.json", "w") as f:
    json.dump(caller.best_config, f)

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('i', type=int)
  parser.add_argument('seed', type=int)
  args = parser.parse_args()
  main(args.i, args.seed)
  