FROM ubuntu:jammy
ARG DEBIAN_FRONTEND=noninterative
RUN apt-get update 
RUN apt-get install -y python3 python3-venv python3-pip r-base
RUN Rscript -e "install.packages('irace', repos='https://cloud.r-project.org')"
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
WORKDIR /usr/app
