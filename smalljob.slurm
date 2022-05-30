#!/bin/bash

#SBATCH --partition=standard
#SBATCH --qos=standard
#SBATCH --cpus-per-task=36
#SBATCH --array=0-5
#SBATCH --time=96:00:00

module load anaconda

cd $SLURM_SUBMIT_DIR

eval "$(conda shell.bash hook)"
conda activate ./.conda

SMALL=smaller python3 smac3_launcher.py $SLURM_ARRAY_TASK_ID
