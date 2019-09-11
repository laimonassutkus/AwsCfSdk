from abc import ABC, abstractmethod
from aws_infrastructure_sdk.lambdas.deployment.deployment_package import DeploymentPackage
from troposphere import GetAtt
from troposphere.awslambda import Function, Code
from troposphere.iam import Role


class AbstractCustomService(ABC):
    def __init__(self, cf_custom_resources_bucket: str, region: str, aws_profile_name: str):
        self.cf_custom_resources_bucket = cf_custom_resources_bucket
        self.region = region
        self.aws_profile_name = aws_profile_name

        self.src = None
        self.lambda_handler = None
        self.lambda_runtime = None
        self.lambda_memory = None
        self.lambda_timeout = None
        self.lambda_description = None
        self.lambda_name = None

    @abstractmethod
    def role(self) -> Role:
        pass

    def function(self) -> Function:
        assert self.lambda_name
        assert self.lambda_handler
        assert self.lambda_runtime
        assert self.lambda_memory
        assert self.lambda_timeout
        assert self.lambda_description

        return Function(
            self.lambda_name,
            Code=Code(
                S3Bucket=self.cf_custom_resources_bucket,
                S3Key=self.lambda_name
            ),
            Handler=self.lambda_handler,
            Role=GetAtt(self.role(), "Arn"),
            Runtime=self.lambda_runtime,
            MemorySize=self.lambda_memory,
            FunctionName=self.lambda_name,
            Timeout=self.lambda_timeout,
            Description=self.lambda_description
        )

    def __deploy_package(self):
        assert self.lambda_name
        assert self.src

        DeploymentPackage(
            environment='none',
            project_src_path=self.src,
            lambda_name=self.lambda_name,
            s3_upload_bucket=self.cf_custom_resources_bucket,
            s3_bucket_region=self.region,
            aws_profile=self.aws_profile_name,
        ).deploy()
