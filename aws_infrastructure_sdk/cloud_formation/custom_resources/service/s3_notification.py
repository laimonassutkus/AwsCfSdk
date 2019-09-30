import os

from aws_infrastructure_sdk.cloud_formation.custom_resources import custom_root_dir
from aws_infrastructure_sdk.cloud_formation.custom_resources.service.abstract_custom_service import AbstractCustomService
from troposphere.iam import Role, Policy


class S3NotificationService(AbstractCustomService):
    def __init__(self):
        super().__init__()

        self.src = os.path.join(
            custom_root_dir,
            'package',
            's3_notification'
        )

        self.lambda_handler = 'index.handler'
        self.lambda_runtime = 'python3.6'
        self.lambda_memory = 128
        self.lambda_timeout = 120
        self.lambda_name = 'CfCustomResourceS3Notification'
        self.lambda_description = (
            'Lambda function enabling AWS CloudFormation to attach a notification configuration to a S3 bucket.'
        )

    def role(self) -> Role:
        return Role(
            "CfCustomResourceS3NotificationLambdaRole",
            Path="/",
            Policies=[Policy(
                PolicyName="CfCustomResourceS3NotificationLambdaPolicy",
                PolicyDocument={
                    "Version": "2012-10-17",
                    "Statement": [{
                        "Action": ["logs:*"],
                        "Resource": "arn:aws:logs:*:*:*",
                        "Effect": "Allow"
                    }, {
                        "Action": [
                            "s3:*",
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
                            "s3.amazonaws.com",
                        ]
                    }
                }
            ]},
        )
