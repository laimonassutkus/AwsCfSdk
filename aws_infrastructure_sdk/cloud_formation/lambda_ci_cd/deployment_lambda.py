from troposphere import Template, GetAtt, Ref
from troposphere.awslambda import Code, Function, Environment
from troposphere.iam import Role, Policy
from aws_infrastructure_sdk.cloud_formation.lambda_ci_cd import lambda_ci_cd_root


class DeploymentLambda:
    """
    A class which provisions an infrastructure for an AWS Lambda function which executes another AWS Lambda
    function deployment from a S3 bucket in which a deployment package resides.
    """
    def __init__(self, prefix: str, lambda_under_deployment: Function) -> None:
        """
        Constructor.

        :param prefix: A prefix for deployment lambda resource names.
        :param lambda_under_deployment: An AWS Lambda function to execute deployments against.
        """
        self.lambda_role = Role(
            prefix + "DeploymentLambdaRole",
            Path="/",
            Policies=[Policy(
                PolicyName=prefix + "DeploymentLambdaRole",
                PolicyDocument={
                    "Version": "2012-10-17",
                    "Statement": [{
                        "Action": ["logs:*"],
                        "Resource": "arn:aws:logs:*:*:*",
                        "Effect": "Allow"
                    }, {
                        "Action": ["lambda:UpdateFunctionCode"],
                        "Resource": "*",
                        "Effect": "Allow"
                    }, {
                        "Action": ["s3:*"],
                        "Resource": "*",
                        "Effect": "Allow"
                    }]
                })],
            AssumeRolePolicyDocument={"Version": "2012-10-17", "Statement": [
                {
                    "Action": ["sts:AssumeRole"],
                    "Effect": "Allow",
                    "Principal": {
                        "Service": [
                            "lambda.amazonaws.com",
                        ]
                    }
                }
            ]},
        )

        self.function = Function(
            prefix + "DeploymentLambda",
            Code=Code(ZipFile=self.__read_template()),
            Handler='index.handler',
            Role=GetAtt(self.lambda_role, "Arn"),
            Runtime='python3.6',
            MemorySize='128',
            FunctionName=prefix + 'DeploymentLambda',
            Timeout='10',
            Environment=Environment(
                Variables={
                    'LAMBDA_FUNCTION_NAME': Ref(lambda_under_deployment)
                }
            ),
            Description=(
                f'Deployment lambda which updates lambda under deployment function code '
                f'from an output from a ci/cd pipeline for {prefix.lower()}.'
            )
        )

    def add(self, template: Template) -> None:
        """
        Adds all created resources to a template.

        :param template: Template to which resources should be added.

        :return: No return.
        """
        template.add_resource(self.function)
        template.add_resource(self.lambda_role)

    @staticmethod
    def __read_template() -> str:
        """
        Reads and returns function code for a deployment AWS Lambda function.

        :return: Source code as a string.
        """
        with open(f'{lambda_ci_cd_root}/deployment.template', 'r') as file:
            return ''.join(file.readlines())
