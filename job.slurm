#!/bin/bash

#SBATCH --partition=standard
#SBATCH --qos=standard
#SBATCH --exclusive
#SBATCH --nodes=1
#SBATCH --tasks-per-node=1
#SBATCH --array=0-5
#SBATCH --time=96:00:00

module load anaconda

cd $SLURM_SUBMIT_DIR

eval "$(conda shell.bash hook)"
conda activate ./.conda

python3 smac3_launcher.py $SLURM_ARRAY_TASK_ID
