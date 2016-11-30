#!/usr/bin/env bash
set -e

# a bash script to run the extract/transform/load scripts on the production
# server.

# activate the environment with the required python libraries
ENV=${1:-reporting}
# if there is no workon home ie: being run by cron, then hardwire the path :(
WORKON_HOME="${WORKON_HOME:-/home/rapporteur/Virtualenvs}"
# shellcheck source=/dev/null
source "$WORKON_HOME/$ENV/bin/activate"

# set stdin, stdout and stderr to be unbuffered.
PYTHONUNBUFFERED=1
export PYTHONUNBUFFERED

# the directory this script is in becomes the pythonpath
PYTHONPATH=$( cd "$(dirname "$0")" ; pwd -P )
export PYTHONPATH

# but we are going work in the home directory of the scripts themselves
cd "${PYTHONPATH}/scripts"
./runner.py all