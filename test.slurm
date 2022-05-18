#!/bin/bash

#SBATCH --partition=standard
#SBATCH --qos=standard
#SBATCH --exclusive
#SBATCH --nodes=6
#SBATCH --tasks-per-node=1
#SBATCH --array=0-5

module load anaconda

python3 probe.py $SLURM_ARRAY_TASK_ID

