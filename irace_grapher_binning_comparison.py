from matplotlib import pyplot as plt
from config import M, sizes, experiment_multiples_dynamic_bin, descent_rates
import json
import sys

def main(i, tuner_seeds, grapher_seeds):
  graph_json_paths = [f"irace_output/performance_binning_comparison_{sizes[i]}_{experiment_multiples_dynamic_bin[i]}_{descent_rates[j]}_{tuner_seeds[j]}_{grapher_seeds[j]}.json" for j in range(M)]
  png_path = f"irace_output/performance_binning_comparison_{sizes[i]}_{experiment_multiples_dynamic_bin[i]}.png"
  performances = [None for j in range(M)]
  for j in range(M):
    with open(graph_json_paths[j]) as f:
      performances[j] = json.load(f)
  figure, ax = plt.subplots(figsize=(12,5))
  figure.subplots_adjust(left=0.25)
  ax.boxplot(performances, labels=descent_rates, vert=False)
  figure.savefig(png_path, dpi=300)

if __name__ == '__main__':
  i = int(sys.argv[1])
  tuner_seeds = list(map(int, sys.argv[2:2+M]))
  grapher_seeds = list(map(int, sys.argv[2+M:2+M+M]))
  main(i, tuner_seeds, grapher_seeds)