#!/usr/bin/env bash

PYTHON=$1

set -e

${PYTHON} setup.py sdist
${PYTHON} -m pip install dist/*

rm -rf *.egg-info build dist
