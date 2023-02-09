import config
import os
from pathlib import Path


Path("output").mkdir(parents=True, exist_ok=True)
for i in range(config.N):
  os.rename(f"output_dynamic_{config.sizes[i]}.txt", f"output/irace_output_dynamic_{config.sizes[i]}_{config.experiment_multiples_dynamic[i]}.txt")
  os.rename(f"output_static_{config.sizes[i]}.txt", f"output/irace_output_static_{config.sizes[i]}_{config.experiment_multiples_static[i]}.txt")
  os.rename(f"irace_dynmaic_{config.sizes[i]}.Rdata", f"output/irace_dynamic_{config.sizes[i]}_{config.experiment_multiples_dynamic[i]}.Rdata")
  os.rename(f"irace_static_{config.sizes[i]}.Rdata", f"output/irace_static_{config.sizes[i]}_{config.experiment_multiples_static[i]}.Rdata")
  os.rename(f"performace_{config.sizes[i]}.json", f"output/performace_{config.sizes[i]}_{config.experiment_multiples_static[i]}_{config.experiment_multiples_dynamic[i]}.json")

