#! /usr/bin/env python3

import subprocess
import os
import sys
output_f = open("output_static.txt", "w")

def main():
    sizes = [10, 100, 1000]

    for size in sizes:
        with open("Instances/1.txt", "w") as f:
            f.write(f"{size}\n")
        
        with open("parameters.txt", "w") as f:
            for i in range(1):
                f.write(f"lbd{i} \"--lbd{i} \" i (1, {size-1}) \n")
        with open("scenario.txt", "w") as f:
            f.write(f"maxExperiments = {size * 10}\n")
            f.write("targetRunner = \"./target_runner_static.py\"\n")
            # f.write(f"debugLevel = 3 \n")
        process = subprocess.Popen(["irace", "--parallel", "12"], stdout=subprocess.PIPE)

        while True:
            try:
                line = next(process.stdout)
                line = line.decode("UTF-8")
                print(line, end="")
                output_f.write(line)
            except StopIteration:
                break

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        output_f.close()
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
    output_f.close()
