FROM debian:bullseye
ARG DEBIAN_FRONTEND=noninterative
RUN apt-get update 
RUN apt-get install -y python3 python3-venv python3-pip r-base build-essential curl
RUN Rscript -e "install.packages('irace', repos='https://cloud.r-project.org')"
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
RUN curl https://sh.rustup.rs -sSf | bash -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"
COPY onell_algs_rs onell_algs_rs
RUN cd onell_algs_rs && maturin build --release && pip3 install target/wheels/onell_algs_rs-*.whl
WORKDIR /usr/app
