curl -O https://repo.anaconda.com/archive/Anaconda3-2021.11-Linux-x86_64.sh
sh Anaconda3-2021.11-Linux-x86_64.sh -b -p ~/anaconda3
~/anaconda3/bin/conda init
source ~/.bashrc
conda install -y R
Rscript -e 'install.packages("irace", repos="https://cloud.r-project.org")'
export PATH="${HOME}/anaconda3/lib/R/library/irace/bin:${PATH}"
PATH_VAR="${HOME}/anaconda3/lib/R/library/irace/bin:\${PATH}"
PATH_VAR="PATH=\"${PATH_VAR}\""
echo $PATH_VAR >> ~/.bashrc
