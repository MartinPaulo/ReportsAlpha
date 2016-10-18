#!/usr/bin/env bash

# activate the environment with the required python libraries
ENV=reporting
source $WORKON_HOME/$ENV/bin/activate

# set stdin, stdout and stderr to be unbuffered.
PYTHONUNBUFFERED=1
export PYTHONUNBUFFERED

# the directory this script is in becomes the pythonpath
export PYTHONPATH=$(pwd)

# but we are going work in the home directory of the scripts themsel
cd scripts
python runner.py