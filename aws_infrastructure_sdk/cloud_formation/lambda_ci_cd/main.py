from typing import List, Dict, Any
from aws_lambda.lambda_cf_creator import LambdaCfFunction
from troposphere import Template
from troposphere.ec2 import SecurityGroup, Subnet
from troposphere.iam import Role
from troposphere.s3 import Bucket
from aws_infrastructure_sdk.cloud_formation.lambda_ci_cd.lambda_pipeline import LambdaPipeline


class LambdaParams:
    """
    AWS Lambda Function parameters that define compute power and other parameters.
    """
    def __init__(
            self,
            description: str,
            memory: int,
            timeout: int,
            handler: str,
            runtime: str,
            role: Role,
            env: Dict[Any, Any],
            security_groups: List[SecurityGroup],
            subnets: List[Subnet]
    ) -> None:
        """
        Constructor.

        :param description: Description of the lambda function.
        :param memory: Memory units for the lambda function.
        :param timeout: Time after which lambda function is terminated if it does not complete.
        :param handler: The name of the main function which will be called to interact with lambda function.
        :param runtime: The type of lambda runtime e.g. python3.6.
        :param role: Role resource that defines what lambda can and can not do.
        :param env: OS-level environment variables for the function.
        :param security_groups: Security groups for the function.
        :param subnets: Subnets in which the function lives. Note, subnets must have NAT Gateway.
        """
        self.role = role
        self.runtime = runtime
        self.handler = handler
        self.timeout = timeout
        self.memory = memory
        self.description = description
        self.env = env
        self.security_groups = security_groups
        self.subnets = subnets


class PipelineParams:
    """
    Parameters class which specifies various parameters for ci/cd pipeline.
    """
    def __init__(self, artifact_builds_bucket: Bucket):
        """
        Constructor.

        :param artifact_builds_bucket: An artifacts bucket which will be used by a ci/cd pipeline to write
        and read build/source artifacts.
        """
        self.artifact_builds_bucket = artifact_builds_bucket


class Main:
    """
    A main project to create a serverless AWS Lambda function with complete CI/CD integration.

    Known pitfalls:
        1. Currently supported only for python.
        2. If your lambda needs internet access - subnets must have a NAT Gateway attached.
    """
    def __init__(
            self,
            prefix: str,
            lambda_params: LambdaParams,
            pipeline_params: PipelineParams
    ):
        self.function = LambdaCfFunction(
            prefix=prefix,
            description=lambda_params.description,
            memory=lambda_params.memory,
            timeout=lambda_params.timeout,
            handler=lambda_params.handler,
            runtime=lambda_params.runtime,
            role=lambda_params.role,
            env=lambda_params.env,
            security_groups=lambda_params.security_groups,
            subnets=lambda_params.subnets
        )

        self.pipeline = LambdaPipeline(
            prefix=prefix,
            lambda_under_deployment=self.function.lambda_function,
            artifacts_bucket=pipeline_params.artifact_builds_bucket
        )

    def add(self, template: Template) -> None:
        """
        Adds all created resources to a template.

        :param template: Template to which resources should be added.

        :return: No return.
        """
        self.function.add(template)
        self.pipeline.add(template)
