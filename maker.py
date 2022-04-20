import subprocess
import os

sizes = [10, 100, 1000]
output_f = open("output.txt", "w")

for size in sizes:
    with open("Instances/1.txt", "w") as f:
        f.write(f"{size}\n")
    
    with open("parameters.txt", "w") as f:
        for i in range(size):
            f.write(f"lbd{i} \"--lbd{1} \" i (1, {size-1}) \n")
    with open("scenario.txt", "w") as f:
        f.write(f"maxExperiments = {size * 100}")
    process = subprocess.Popen(["irace", "--parallel", "12"], stdout=subprocess.PIPE)

    while True:
        try:
            line = next(process.stdout)
            line = line.decode("UTF-8")
            print(line, end="")
            output_f.write(line)
        except StopIteration:
            break
    break

output_f.close()
