#!/usr/bin/env bash

# This script uploads an AWS Lambda deployment package to an
# S3 bucket and updates a Lambda function.

LAMBDA_NAME=$1; shift;
S3_BUCKET=$1; shift;
AWS_PROFILE_NAME=$1; shift;
AWS_REGION=$1; shift;

# This is the default path where lambda build are made.
# These two exact lines are specified in the build.sh script.
# Make sure they are synchronized.
ROOT_PATH="/tmp/aws-infrastructure-sdk/lambda/deployment"
BUILD_PATH=${ROOT_PATH}"/package.zip"

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
