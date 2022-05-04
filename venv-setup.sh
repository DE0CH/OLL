#!/usr/bin/env bash 

SOURCE=${BASH_SOURCE[0]}
while [ -h "$SOURCE" ]; do # resolve $SOURCE until the file is no longer a symlink
  DIR=$( cd -P "$( dirname "$SOURCE" )" >/dev/null 2>&1 && pwd )
  SOURCE=$(readlink "$SOURCE")
  [[ $SOURCE != /* ]] && SOURCE=$DIR/$SOURCE # if $SOURCE was a relative symlink, we need to resolve it relative to the path where the symlink file was located
done
DIR=$( cd -P "$( dirname "$SOURCE" )" >/dev/null 2>&1 && pwd )

[[ $ZSH_EVAL_CONTEXT =~ :file$ ]] || (echo "Run this as source" && exit 1)
python3 -m venv ${DIR}/venv 
source ${DIR}venv/bin/activate
pip3 install -r ${DIR}/requirement.txt