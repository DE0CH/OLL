#!/usr/bin/env bash

module load anaconda
eval "$(conda shell.bash hook)"
conda create --prefix=./.conda python
conda activate ./.conda
conda install gxx_linux-64 gcc_linux-64 swig
pip3 install -r requirements.txt
