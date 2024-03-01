#!/bin/bash

set -e

reset_color="\033[00m"
black="\033[30m"
red="\033[31m"
green="\033[32m"
yellow="\033[33m"
blue="\033[34m"
magenta="\033[35m"
cyan="\033[36m"
white="\033[37m"

if [[ -z $PYTHON ]]; then
    PYTHON=python3
fi

clear
echo -e """${green}
==========================
Python Virtual Environment
==========================
${reset_color}"""

sleep 1

### Get rid of caches NOT in .venv
echo -e """${cyan}
    Cleaning cached pyc files
${reset_color}"""
find . -type d ! -path './.venv/*' -name '__pycache__' -exec rm -rf {} +
find . -type d ! -path './.venv/*' -name '.pytest_cache' -exec rm -rf {} +
find . -type d ! -path './.venv/*' -name '.mypy_cache' -exec rm -rf {} +

### Check for existence of `.venv` dir
if [[ ! -d $PWD/.venv ]]; then
    echo -e """${cyan}
    Virtual environment not found -- Creating ".venv"
${reset_color}"""
    $PYTHON -m venv .venv --prompt=sbn-survey-image-service
else
    echo -e """${cyan}
    Virtual environment found in ".venv"
${reset_color}"""
fi

### Activate VENV
source ./.venv/bin/activate

### Install package dependencies for project

echo -e """${green}
===========================
Setup dependencies and code
===========================
${reset_color}"""

pip install --upgrade -q -q -q pip setuptools wheel
pip install -e .[recommended,dev]

if [[ ! -e $VIRTUAL_ENV/bin/fitscut ]]; then
    echo -e """${cyan}
    Installing fitscut
${reset_color}
"""
    ./_install_fitscut
fi

### Link git pre-commit-hook script
ln -fs $PWD/_precommit_hook $PWD/.git/hooks/pre-commit

if [ ! -f $PWD/.env ]; then
    echo -e """${red}
To create a .env file:

    source .venv/bin/activate
    _sbnsis env

Then edit .env
${reset_color}"""
fi

### 7. Final Message
echo -e """${cyan}
    Done. Bon courage!
${reset_color}
"""