import irace_grapher
import argparse
from config import N

if __name__ == '__main__':
  parser = argparse.ArgumentParser("Graph graphs based on the cached json files")
  parser.add_argument('graphs_path', default='irace_output')
  args = parser.parse_args()
  for i in range(N):
    irace_grapher.main(i, -1, -1, -1, -1, args.graphs_path)

