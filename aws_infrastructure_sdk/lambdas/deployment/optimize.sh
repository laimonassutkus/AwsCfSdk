#!/usr/bin/env bash

# This script contains various optimization functions
# for AWS Lambda deployment package.

# Usually pip is no longer needed in AWS Lambda package.
function omit_pip() {
    PATH_TO_BUILD="$1"

    rm -rf "$PATH_TO_BUILD/pip"
    rm -rf "$PATH_TO_BUILD/pip-*"
}

# Usually setup tools are no longer needed in AWS Lambda package.
function omit_setup() {
    PATH_TO_BUILD="$1"

    rm -rf "$PATH_TO_BUILD/setuptools"
    rm -rf "$PATH_TO_BUILD/setuptools-*"
}

# Usually wheel functionality is no longer needed in AWS Lambda package.
function omit_wheel() {
    PATH_TO_BUILD="$1"

    rm -rf "$PATH_TO_BUILD/wheel"
    rm -rf "$PATH_TO_BUILD/wheel-*"
}

# Usually boto and botocore are already provided in the AWS Lambda environment and are not needed
# to include in the deployment package. Please note, that AWS Lambda environment's boto and botocore
# versions are usually out-dated, therefore it is highly recommended to include boto and botocore
# in the deployment package.
function omit_boto() {
    PATH_TO_BUILD="$1"

    rm -rf "$PATH_TO_BUILD/boto3"
    rm -rf "$PATH_TO_BUILD/boto3-*"
    rm -rf "$PATH_TO_BUILD/botocore"
    rm -rf "$PATH_TO_BUILD/botocore-*"
}
