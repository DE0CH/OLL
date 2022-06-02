import config
import matplotlib.pyplot as plt
import os
import json

def graph(n, static_multiple, dynamic_multiple):

  # Load the performance file
  with open(f"performace_{n}_{static_multiple}_{dynamic_multiple}.json") as f:
    static_lbd_performace, dynamic_lbd_performace, random_lbd_performace, random_lbd_same_performace, one_lbd_performace, dynamic_theory_performace, five_param_performace = json.load(f)
  
  # Plot the Graph
  figure, ax = plt.subplots(figsize=(12,5))
  figure.subplots_adjust(left=0.25)
  ax.boxplot(
    (static_lbd_performace, dynamic_lbd_performace, random_lbd_performace, one_lbd_performace, dynamic_theory_performace, five_param_performace), 
    labels=(f"Static Lambda", "Dynamic Lambda", "Random Lambda", "Lambda = 1", "Dynamic Theory", "Five Parameters"), 
    vert=False
  )
  
  # Save the figure
  figure.savefig(f"box_plot_{n}_{static_multiple}_{dynamic_multiple}.pdf")

def main():

  # Iterate over all the configs
  for i in range(config.N):
    graph(config.sizes[i], config.experiment_multiples_static[i], config.experiment_multiples_dynamic[i])

if __name__ == '__main__':
  os.chdir(os.path.dirname(__file__))
  exit(main())