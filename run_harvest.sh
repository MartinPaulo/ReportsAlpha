#!/usr/bin/env bash

# a bash script to run the extract/transform/load scripts on the production
# server.

# activate the environment with the required python libraries
ENV=reporting
source $WORKON_HOME/$ENV/bin/activate

# set stdin, stdout and stderr to be unbuffered.
PYTHONUNBUFFERED=1
export PYTHONUNBUFFERED

# the directory this script is in becomes the pythonpath
export PYTHONPATH=$( cd $(dirname $0) ; pwd -P )

# but we are going work in the home directory of the scripts themselves
cd scripts
python runner.py