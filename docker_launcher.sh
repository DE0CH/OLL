#!/bin/bash

docker build -t oll . && docker run -it -v ${PWD}:/usr/app oll
