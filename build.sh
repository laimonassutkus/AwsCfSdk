#!/usr/bin/env bash

rm -rf *.egg-info build dist

set -e

python3 setup.py bdist_wheel sdist

while getopts 'iu' flag; do
  case "${flag}" in
    i) python3 -m pip install . ;;
    u) twine upload dist/* ;;
    *) echo 'Unexpected flag.'
       exit 1 ;;
  esac
done
