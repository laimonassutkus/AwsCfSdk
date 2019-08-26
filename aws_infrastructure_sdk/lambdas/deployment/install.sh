#!/usr/bin/env bash

# This script installs a given project
# to a given python environment.

PYTHON=$1
ENVIRONMENT=$2
PROJECT_PATH=$3

set -e

# Save the original path so later we can back here.
tmp_path=$( pwd )
# Go to the provided project path and do all actions in that directory.
cd $PROJECT_PATH
# Remove leftovers.
rm -rf *.egg-info build dist
# Create project's source distribution.
# Read more about this command here:
# https://docs.python.org/3.6/distutils/sourcedist.html
${PYTHON} setup.py sdist

if [[ "$ENVIRONMENT" = "none" ]]; then
    # Install the package.
    # Read more about installing python packages here:
    # https://packaging.python.org/tutorials/installing-packages/
    ${PYTHON} -m pip install dist/*
elif [[ "$ENVIRONMENT" = "dev" || "$ENVIRONMENT" = "prod" ]]
then
    # Install the package by passing custom options with "install-option".
    # Read more about this:
    # https://pip.pypa.io/en/stable/reference/pip_install/#id30
    ${PYTHON} -m pip install dist/* --install-option=--environment=$ENVIRONMENT
else
    echo "Unsupported environment - should be prod or dev."
    # Remove leftovers.
    rm -rf *.egg-info build dist
    exit 1
fi

# Remove leftovers.
rm -rf *.egg-info build dist
# Get back to the original path.
cd $tmp_path
