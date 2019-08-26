import os
import subprocess
import logging

from typing import Optional
from aws_infrastructure_sdk.lambdas.deployment import lambda_deployment_dir
from aws_infrastructure_sdk.s3.s3_bucket_creator import S3BucketCreator

logr = logging.getLogger(__name__)


class DeploymentPackage:
    def __init__(
            self,
            project_src_path: str,
            lambda_name: str,
            s3_upload_bucket: str,
            s3_bucket_region: str,
            aws_profile: str,
            environment: Optional[str] = None,
            refresh_lambda: bool = False
    ) -> None:
        self.__refresh_lambda = refresh_lambda
        self.__aws_profile = aws_profile
        self.__environment = environment or ''
        self.__s3_upload_bucket = s3_upload_bucket
        self.__s3_bucket_region = s3_bucket_region
        self.__project_src_path = project_src_path
        self.__lambda_name = lambda_name
        self.__dir = lambda_deployment_dir

        self.__build_command = [
            os.path.join(self.__dir, 'build.sh'),
            self.__environment,
            self.__project_src_path
        ]

        upload_options = ['-s']
        if self.__refresh_lambda:
            upload_options.append('-l')

        self.__upload_command = [
            os.path.join(self.__dir, 'upload.sh'),
            self.__lambda_name,
            self.__s3_upload_bucket,
            self.__aws_profile,
            self.__s3_bucket_region
        ]

        self.__upload_command.extend(upload_options)

    def deploy(self):
        # Actually we do not have to check what type of environment is passed. The script will assert this
        # part and throw an exception if the value is not valid. However this is purely optimization part
        # which would save quite some time if an incorrect environment is provided. If installation
        # scripts tend to change and support more environments - delete or update the line below.
        assert self.__environment in ['dev', 'prod', 'none'], 'Unsuppored env!'

        # Ensure that provided bucket exists.
        S3BucketCreator(self.__s3_upload_bucket, self.__s3_bucket_region).create()

        try:
            logr.info('Installing...')
            output = subprocess.check_output(self.__build_command, stderr=subprocess.STDOUT)
            logr.info(output.decode())

            logr.info('Uploading...')
            output = subprocess.check_output(self.__upload_command, stderr=subprocess.STDOUT)
            logr.info(output.decode())
        except subprocess.CalledProcessError as ex:
            logr.error(ex.output.decode())
            raise
