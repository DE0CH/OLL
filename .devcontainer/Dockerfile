FROM debian:bullseye

RUN apt-get update
RUN apt-get install -y git sudo zsh thefuck bash curl htop
RUN echo "vscode ALL=(ALL:ALL) NOPASSWD:ALL" >> /etc/sudoers

RUN useradd -m vscode -s /bin/zsh 

USER vscode 
RUN /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/DE0CH/dotfiles/master/setup-zsh.sh)"
RUN echo 'eval $(thefuck --alias)' >> /home/vscode/.zshrc
WORKDIR /home/vscode

USER root
# Project specific stuff
RUN apt-get install -y python3 python3-pip r-base
RUN pip3 install wheel maturin

USER vscode
RUN curl https://sh.rustup.rs -sSf | sh -s -- -y

USER root
RUN Rscript -e "install.packages('irace', repos='https://cloud.r-project.org')"
