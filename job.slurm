#!/bin/bash

#SBATCH --partition=standard
#SBATCH --qos=standard
#SBATCH --cpus-per-task=36
#SBATCH --array=0-5

module load anaconda

cd $SLURM_SUBMIT_DIR

eval "$(conda shell.bash hook)"
conda activate ./.conda

python3 smac3_launcher.py $SLURM_ARRAY_TASK_ID
