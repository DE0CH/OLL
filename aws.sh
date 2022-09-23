#!/usr/bin/env bash

sudo apt-get update 
sudo apt-get install -y python3 python3-pip r-base curl build-essential htop

curl https://sh.rustup.rs -sSf | bash -s -- -y

export PATH="$HOME/.cargo/bin:$PATH"
echo 'PATH="$HOME/.cargo/bin:$PATH"' > ~/.bashrc

sudo pip3 install -r requirements.txt
sudo Rscript -e "install.packages('irace', repos='https://cloud.r-project.org')" 

cd onell_algs_rs && rm -rf target && maturin build --release && sudo pip install target/wheels/* && cd ..

rm -rf irace_output

