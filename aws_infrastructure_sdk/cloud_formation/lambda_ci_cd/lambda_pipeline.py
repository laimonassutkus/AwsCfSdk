from aws_cf_custom_resources.s3_notification.resource import CustomS3Notification
from aws_cf_custom_resources.s3_notification.service import S3NotificationService
from troposphere import GetAtt, Template
from troposphere.awslambda import Function, Permission
from troposphere.codebuild import Project, Artifacts, Environment, Source
from troposphere.codecommit import Repository
from troposphere.codepipeline import *
from troposphere.iam import Role, Policy
from troposphere.s3 import Bucket, PublicAccessBlockConfiguration
from aws_infrastructure_sdk.cloud_formation.lambda_ci_cd import lambda_ci_cd_root
from aws_infrastructure_sdk.cloud_formation.lambda_ci_cd.deployment_lambda import DeploymentLambda


class LambdaPipeline:
    """
    A main ci/cd pipeline class.
    """
    RUNTIME_TO_BUILD_SPECS_MAP = {
        'python3.6': 'python-buildspec.yml',
        'python3.7': 'python-buildspec.yml',
    }

    def __init__(
            self,
            prefix: str,
            lambda_under_deployment: Function,
            artifacts_bucket: Bucket
    ) -> None:
        """
        Constructor.

        :param prefix: A prefix for pipeline resource names.
        :param lambda_under_deployment: Main AWS Lambda function for which the pipeline should be created.
        :param artifacts_bucket: An S3 bucket in which pipeline builds are saved and read.
        """
        self.lambda_under_deployment = lambda_under_deployment

        self.deployment_group_role = Role(
            prefix + 'DeploymentGroupRole',
            Path='/',
            Policies=[Policy(
                PolicyName=prefix + 'FargateEcsDeploymentGroupPolicy',
                PolicyDocument={
                    'Version': '2012-10-17',
                    'Statement': [{
                        'Action': [
                            "lambda:InvokeFunction",
                            "cloudwatch:DescribeAlarms",
                            "sns:Publish",
                            "s3:GetObject",
                            "s3:GetObjectMetadata",
                            "s3:GetObjectVersion",
                            "iam:PassRole"
                        ],
                        "Resource": "*",
                        "Effect": "Allow"
                    }]
                })],
            AssumeRolePolicyDocument={'Version': '2012-10-17', 'Statement': [
                {
                    'Action': ['sts:AssumeRole'],
                    'Effect': 'Allow',
                    'Principal': {
                        'Service': [
                            'codedeploy.amazonaws.com',
                        ]
                    }
                }
            ]},
        )

        self.code_build_role = Role(
            prefix + 'CodeBuildRole',
            Path='/',
            Policies=[Policy(
                PolicyName=prefix + 'CodeBuildPolicy',
                PolicyDocument={
                    'Version': '2012-10-17',
                    'Statement': [{
                        'Effect': 'Allow',
                        'Action': ['codebuild:*'],
                        'Resource': '*'
                    }, {
                        "Effect": "Allow",
                        "Action": ["logs:*"],
                        "Resource": "arn:aws:logs:*:*:*"
                    }, {
                        'Effect': 'Allow',
                        'Action': ['s3:*'],
                        'Resource': '*'
                    }, {
                        'Effect': 'Allow',
                        'Action': ['ssm:*'],
                        'Resource': '*'
                    }]
                })],
            AssumeRolePolicyDocument={'Version': '2012-10-17', 'Statement': [
                {
                    'Action': ['sts:AssumeRole'],
                    'Effect': 'Allow',
                    'Principal': {
                        'Service': [
                            'codebuild.amazonaws.com',
                        ]
                    }
                }
            ]},
        )

        self.pipeline_role = Role(
            prefix + 'PipelineRole',
            Path='/',
            Policies=[Policy(
                PolicyName=prefix + 'PipelinePolicy',
                PolicyDocument={
                    'Version': '2012-10-17',
                    'Statement': [{
                        'Effect': 'Allow',
                        'Action': 'codepipeline:*',
                        'Resource': '*'
                    }, {
                        'Effect': 'Allow',
                        'Action': 'codecommit:*',
                        'Resource': '*'
                    }, {
                        'Effect': 'Allow',
                        'Action': 's3:*',
                        'Resource': '*'
                    }, {
                        'Effect': 'Allow',
                        'Action': 'codebuild:*',
                        'Resource': '*'
                    }]
                })],
            AssumeRolePolicyDocument={'Version': '2012-10-17', 'Statement': [
                {
                    'Action': ['sts:AssumeRole'],
                    'Effect': 'Allow',
                    'Principal': {
                        'Service': [
                            'codepipeline.amazonaws.com',
                        ]
                    }
                }
            ]},
        )

        # Create a bucket to which a ci/cd pipeline will save a build output (Lambda deployment package).
        self.lambda_deployment_bucket = Bucket(
            prefix + 'LambdaDeploymentBucket',
            BucketName=prefix.lower() + '.lambda.deployment.bucket',
            AccessControl='Private',
            PublicAccessBlockConfiguration=PublicAccessBlockConfiguration(
                BlockPublicAcls=True,
                BlockPublicPolicy=True,
                IgnorePublicAcls=True,
                RestrictPublicBuckets=True
            )
        )

        # Create deployment lambda which executes deployment actions against our original AWS Lambda function.
        self.lambda_deployment_bucket_trigger = DeploymentLambda(prefix, lambda_under_deployment)

        # We need to create an explicit permission for a S3 bucket so the bucket would be able to
        # invoke deployment lambda function.
        self.invoke_permission = Permission(
            prefix + 'LambdaDeploymentPermission',
            Action='lambda:InvokeFunction',
            FunctionName=GetAtt(self.lambda_deployment_bucket_trigger.function, 'Arn'),
            Principal='s3.amazonaws.com',
            SourceArn=GetAtt(self.lambda_deployment_bucket, 'Arn')
        )

        # Add a notification configuration to our S3 bucket which makes the bucket to fire an event and invoke
        # the deployment function every time an object is created in the bucket.
        self.s3_notification_configuration = CustomS3Notification(
            prefix + 'S3NotificationConfiguration',
            ServiceToken=S3NotificationService().service_token(),
            BucketName=self.lambda_deployment_bucket.BucketName,
            NotificationConfiguration={
                'LambdaFunctionConfigurations': [
                    {
                        'LambdaFunctionArn': GetAtt(self.lambda_deployment_bucket_trigger.function, 'Arn'),
                        'Events': [
                            's3:ObjectCreated:*',
                        ],
                    },
                ]
            },
            DependsOn=[
                self.lambda_deployment_bucket.title,
                self.invoke_permission.title,
                self.lambda_deployment_bucket_trigger.function.title
            ]
        )

        # Create a main git repository which fires a ci/cd pipeline every time a code is committed to it.
        self.git_repository = Repository(
            prefix + 'GitRepository',
            RepositoryName=prefix.lower()
        )

        self.code_build_project = Project(
            prefix + 'CodeBuildProject',
            Name=prefix + 'CodeBuildProject',
            Artifacts=Artifacts(
                Type='CODEPIPELINE'
            ),
            Environment=Environment(
                ComputeType='BUILD_GENERAL1_SMALL',
                Image='aws/codebuild/standard:2.0',
                Type='LINUX_CONTAINER',
                EnvironmentVariables=[],
            ),
            ServiceRole=GetAtt(self.code_build_role, 'Arn'),
            Source=Source(
                Type='CODEPIPELINE',
                BuildSpec=self.__read_buildspec()
            )
        )

        # Our main pipeline for ci/cd.
        self.pipeline = Pipeline(
            prefix + 'Pipeline',
            ArtifactStore=ArtifactStore(
                Location=artifacts_bucket.BucketName,
                Type='S3'
            ),
            Name=prefix + 'Pipeline',
            RoleArn=GetAtt(self.pipeline_role, 'Arn'),
            Stages=[
                Stages(
                    Name='SourceStage',
                    Actions=[
                        Actions(
                            Name='SourceAction',
                            ActionTypeId=ActionTypeId(
                                Category='Source',
                                Owner='AWS',
                                Version='1',
                                Provider='CodeCommit'
                            ),
                            OutputArtifacts=[
                                OutputArtifacts(
                                    Name='SourceOutput'
                                )
                            ],
                            Configuration={
                                'RepositoryName': self.git_repository.RepositoryName,
                                'BranchName': 'master'
                            },
                            RunOrder='1'
                        )
                    ]
                ),
                Stages(
                    Name='BuildStage',
                    Actions=[
                        Actions(
                            Name='BuildAction',
                            ActionTypeId=ActionTypeId(
                                Category='Build',
                                Owner='AWS',
                                Version='1',
                                Provider='CodeBuild'
                            ),
                            InputArtifacts=[
                                InputArtifacts(
                                    Name='SourceOutput'
                                )
                            ],
                            OutputArtifacts=[
                                OutputArtifacts(
                                    Name='BuildOutput'
                                )
                            ],
                            Configuration={
                                'ProjectName': self.code_build_project.Name,
                            },
                            RunOrder='1'
                        )
                    ]
                ),
                Stages(
                    Name='DeployStage',
                    Actions=[
                        Actions(
                            Name='DeployAction',
                            ActionTypeId=ActionTypeId(
                                Category='Deploy',
                                Owner='AWS',
                                Version='1',
                                Provider='S3'
                            ),
                            InputArtifacts=[
                                InputArtifacts(
                                    Name='BuildOutput'
                                )
                            ],
                            Configuration={
                                'BucketName': self.lambda_deployment_bucket.BucketName,
                                'Extract': False,
                                'ObjectKey': 'package.zip'
                            },
                            RunOrder='1'
                        )
                    ]
                )
            ],
            DependsOn=[
                artifacts_bucket.title,
                self.git_repository.title,
                self.code_build_project.title,
                lambda_under_deployment.title
            ]
        )

    def add(self, template: Template) -> None:
        """
        Adds all created resources to a template.

        :param template: Template to which resources should be added.

        :return: No return.
        """
        self.lambda_deployment_bucket_trigger.add(template)

        template.add_resource(self.pipeline_role)
        template.add_resource(self.code_build_role)
        template.add_resource(self.deployment_group_role)
        template.add_resource(self.lambda_deployment_bucket)
        template.add_resource(self.invoke_permission)
        template.add_resource(self.s3_notification_configuration)
        template.add_resource(self.git_repository)
        template.add_resource(self.code_build_project)
        template.add_resource(self.pipeline)

    def __read_buildspec(self) -> str:
        """
        Reads and returns buildspec config for build project..

        :return: Buildspec config as a string.
        """
        runtime = self.RUNTIME_TO_BUILD_SPECS_MAP.get(self.lambda_under_deployment.Runtime)
        if not runtime:
            raise ValueError(f'This runtime ({self.lambda_under_deployment.Runtime}) is currently not supported.')

        with open(f'{lambda_ci_cd_root}/{runtime}', 'r') as file:
            return ''.join(file.readlines())
