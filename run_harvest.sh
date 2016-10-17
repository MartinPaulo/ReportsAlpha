#!/usr/bin/env bash

# set stdin, stdout and stderr to be unbuffered.
PYTHONUNBUFFERED=1
export PYTHONUNBUFFERED

# the directory this script is in
export PYTHONPATH=$(pwd)

echo $PYTHONPATH

cd scripts
python runner.py