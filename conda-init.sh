#!/usr/bin/env bash

module load anaconda
eval "$(conda shell.bash hook)"
conda create --prefix=./.conda -y
conda activate ./.conda
conda install -y gxx_linux-64 gcc_linux-64 swig
pip3 install -r requirements.txt
