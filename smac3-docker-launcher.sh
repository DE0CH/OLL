#!/bin/bash

docker build -f Dockerfile.smac3 -t oll-smac3 . && docker run -it -v ${PWD}:/usr/app oll-smac3
