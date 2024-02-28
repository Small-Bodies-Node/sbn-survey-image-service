#!/usr/bin/env false

### 0. Load vars defined in .env
if [ ! -f $PWD/.env ]; then
    echo -e "No .env file found.  Generate with '_sbnsis env' then edit."
    return 1
fi
source .env

### 1. Message user
clear
echo -e """${GRE}
==========================
Python Virtual Environment
==========================
${WHI}"""

sleep 1

### 2. Get rid of caches NOT in .venv
echo -e """${BLU}
    Cleaning cached pyc files
${WHI}"""
find . -type d ! -path './.venv/*' -name '__pycache__' -exec rm -rf {} +
find . -type d ! -path './.venv/*' -name '.pytest_cache' -exec rm -rf {} +
find . -type d ! -path './.venv/*' -name '.mypy_cache' -exec rm -rf {} +

### 3. Check for existence of `.venv` dir
if [[ ! -d $PWD/.venv ]]; then
    echo -e """${BLU}
    Virtual environment not found -- Creating ".venv"
${WHI}"""
    $PYTHON_3_6_OR_HIGHER -m venv .venv --prompt=$APP_NAME
else
    echo -e """${BLU}
    Virtual environment found in ".venv"
${WHI}"""
fi

### 4. Activate VENV
source ./.venv/bin/activate

### 5. Install package dependencies for project

echo -e """${GRE}
===========================
Setup dependencies and code
===========================
${WHI}"""

pip install --upgrade -q -q -q pip setuptools wheel
pip install -e .[recommended,dev]

if [[ ! -e $VIRTUAL_ENV/bin/fitscut ]]; then
    echo -e """${BLU}
    installing fitscut
${WHI}
"""
    ./_install_fitscut
fi

### 6. Link git pre-commit-hook script
ln -fs $PWD/_precommit_hook $PWD/.git/hooks/pre-commit

### 7. Final Message
echo -e """${BLU}
    Done. Bon courage!
${WHI}
"""
