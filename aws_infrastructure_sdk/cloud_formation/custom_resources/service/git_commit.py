import os

from aws_infrastructure_sdk.cloud_formation.custom_resources import custom_root_dir
from aws_infrastructure_sdk.cloud_formation.custom_resources.service.abstract_custom_service import AbstractCustomService
from troposphere.iam import Role, Policy


class GitCommitService(AbstractCustomService):
    def __init__(self):
        super().__init__()

        self.src = os.path.join(
            custom_root_dir,
            'package',
            'git_commit'
        )

        self.lambda_handler = 'index.handler'
        self.lambda_runtime = 'python3.6'
        self.lambda_memory = 128
        self.lambda_timeout = 120
        self.lambda_name = 'CfCustomResourceGitCommit'
        self.lambda_description = (
            'Lambda function enabling AWS CloudFormation to create commits to git repositories.'
        )

    def role(self) -> Role:
        return Role(
            "CfCustomResourceGitCommitLambdaRole",
            Path="/",
            Policies=[Policy(
                PolicyName="CfCustomResourceGitCommitLambdaPolicy",
                PolicyDocument={
                    "Version": "2012-10-17",
                    "Statement": [{
                        "Action": ["logs:*"],
                        "Resource": "arn:aws:logs:*:*:*",
                        "Effect": "Allow"
                    }, {
                        "Action": [
                            "codecommit:CreateCommit",
                            "codecommit:GetBranch",
                        ],
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
