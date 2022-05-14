#!/bin/bash

docker build -f Dockerfile.smac3 -t oll-smac3 . && docker run -e SMALL=$SMALL -it -v ${PWD}:/usr/app oll-smac3
