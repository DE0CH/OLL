#!/bin/bash

#SBATCH --partition=standard
#SBATCH --qos=standard
#SBATCH --exclusive
#SBATCH --nodes=6
#SBATCH --tasks-per-node=1
#SBATCH --array=0-5

module load anaconda

cd $SLURM_SUBMIT_DIR

eval "$(conda shell.bash hook)"
conda activate ./.conda

python3 smac3_launcher.py

