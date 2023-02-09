#!/bin/bash

docker build -f Dockerfile.irace -t oll-irace . && docker run -it -v ${PWD}:/usr/app oll-irace
