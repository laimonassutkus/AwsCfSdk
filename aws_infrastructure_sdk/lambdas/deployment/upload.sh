#!/usr/bin/env bash

# This script uploads an AWS Lambda deployment package to an
# S3 bucket and updates a Lambda function.

# The name of the AWS Lambda function which is going to be updated with the new build.
LAMBDA_NAME=$1; shift;
# An AWS S3 bucket in which the new build is going to be uploaded.
S3_BUCKET=$1; shift;
# A profile name by which credentials should be found on this machine.
AWS_PROFILE_NAME=$1; shift;
# An AWS region in which an S3 bucket and the AWS Lambda function exists.
AWS_REGION=$1; shift;
# A full path to a build file (e.g. /tmp/my-build.zip).
BUILD_PATH=$1; shift;

set -e

# Assert project name.
if ! [[ -n "$LAMBDA_NAME" ]]; then
    echo "Lambda name is empty!"
    exit 1
fi

# Assert build path.
if [[ ! -f ${BUILD_PATH} ]]; then
    echo "Build file $BUILD_PATH not found! Did you forget to run build.sh?"
fi

while getopts "sl" flag; do
  case "${flag}" in
    s) aws s3 cp $BUILD_PATH s3://"$S3_BUCKET"/"$LAMBDA_NAME" --profile "$AWS_PROFILE_NAME"  --region "$AWS_REGION";;
    l) aws lambda update-function-code --function-name="$LAMBDA_NAME" --s3-bucket="$S3_BUCKET" --s3-key="$LAMBDA_NAME" --publish --profile "$AWS_PROFILE_NAME" --region "$AWS_REGION";;
    *) echo "Unexpected flag."
       exit 1 ;;
  esac
done

rm $BUILD_PATH
