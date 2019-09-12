from troposphere.awslambda import Function
from troposphere.codecommit import Repository as GitRepository
from troposphere.ecr import Repository as EcrRepository
from troposphere.codedeploy import Application
from troposphere.elasticloadbalancingv2 import TargetGroup, Listener
from troposphere.iam import Role, Policy
from troposphere import Template, GetAtt, Ref
from troposphere.codepipeline import *
from aws_infrastructure_sdk.cloud_formation.custom_resources.resource.deployment_group import CustomDeploymentGroup


class EcsPipeline:
    def __init__(
            self,
            prefix: str,
            custom_deployment_group_lambda_function: Function,
            main_target_group: TargetGroup,
            deployments_target_group: TargetGroup,
            main_listener: Listener,
            deployments_listener: Listener,
            ecs_service_name: str,
            ecs_cluster_name: str,
            artifact_builds_s3: str,
    ):
        self.deployment_group_role = Role(
            prefix + 'FargateEcsDeploymentGroupRole',
            Path='/',
            Policies=[Policy(
                PolicyName=prefix + 'FargateEcsDeploymentGroupPolicy',
                PolicyDocument={
                    'Version': '2012-10-17',
                    'Statement': [{
                        'Action': [
                            "ecs:DescribeServices",
                            "ecs:CreateTaskSet",
                            "ecs:UpdateServicePrimaryTaskSet",
                            "ecs:DeleteTaskSet",
                            "elasticloadbalancing:DescribeTargetGroups",
                            "elasticloadbalancing:DescribeListeners",
                            "elasticloadbalancing:ModifyListener",
                            "elasticloadbalancing:DescribeRules",
                            "elasticloadbalancing:ModifyRule",
                            "lambda:InvokeFunction",
                            "cloudwatch:DescribeAlarms",
                            "sns:Publish",
                            "s3:GetObject",
                            "s3:GetObjectMetadata",
                            "s3:GetObjectVersion"
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
                            'ecs-tasks.amazonaws.com',
                            'codedeploy.amazonaws.com',
                        ]
                    }
                }
            ]},
        )

        self.pipeline_role = Role(
            prefix + 'FargateEcsPipelineRole',
            Path='/',
            Policies=[Policy(
                PolicyName=prefix + 'FargateEcsPipelinePolicy',
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
                    }, {
                        'Effect': 'Allow',
                        'Action': 'codedeploy:*',
                        'Resource': '*'
                    }, {
                        'Effect': 'Allow',
                        'Action': 'ecs:*',
                        'Resource': '*'
                    }, {
                        'Effect': 'Allow',
                        'Action': 'ecr:*',
                        'Resource': '*'
                    }, {
                        'Effect': 'Allow',
                        'Action': 'ec2:*',
                        'Resource': '*'
                    }, {
                        'Effect': 'Allow',
                        'Action': 'iam:*',
                        'Resource': '*'
                    }, {
                        'Effect': 'Allow',
                        'Action': 'elasticloadbalancing:*',
                        'Resource': '*'
                    }, {
                        'Effect': 'Allow',
                        'Action': 'logs:*',
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
                            'codecommit.amazonaws.com',
                            'codebuild.amazonaws.com',
                            'codedeploy.amazonaws.com',
                            'ecs-tasks.amazonaws.com',
                            'iam.amazonaws.com',
                            'ecs.amazonaws.com',
                            's3.amazonaws.com',
                            'ec2.amazonaws.com'
                        ]
                    }
                }
            ]},
        )

        self.git_repository = GitRepository(
            prefix + 'FargateEcsGitRepository',
            RepositoryDescription=(
                'Repository containing appspec and taskdef files for ecs code-deploy blue/green deployments.'
            ),
            RepositoryName=prefix.lower()
        )

        self.ecr_repository = EcrRepository(
            prefix + 'FargateEcsEcrRepository',
            RepositoryName=prefix.lower()
        )

        self.application = Application(
            prefix + 'FargateEcsCodeDeployApplication',
            ApplicationName=prefix + 'FargateEcsCodeDeployApplication',
            ComputePlatform='ECS'
        )

        self.deployment_group = CustomDeploymentGroup(
            prefix + 'FargateEcsDeploymentGroup',
            ServiceToken=GetAtt(custom_deployment_group_lambda_function, 'Arn'),
            ApplicationName=self.application.ApplicationName,
            DeploymentGroupName=prefix + 'FargateEcsDeploymentGroup',
            DeploymentConfigName='CodeDeployDefault.ECSAllAtOnce',
            ServiceRoleArn=GetAtt(self.deployment_group_role, 'Arn'),
            AutoRollbackConfiguration={
                'enabled': True,
                'events': ['DEPLOYMENT_FAILURE', 'DEPLOYMENT_STOP_ON_ALARM', 'DEPLOYMENT_STOP_ON_REQUEST']
            },
            DeploymentStyle={
                'deploymentType': 'BLUE_GREEN',
                'deploymentOption': 'WITH_TRAFFIC_CONTROL'
            },
            BlueGreenDeploymentConfiguration={
                'terminateBlueInstancesOnDeploymentSuccess': {
                    'action': 'TERMINATE',
                    'terminationWaitTimeInMinutes': 5
                },
                'deploymentReadyOption': {
                    'actionOnTimeout': 'CONTINUE_DEPLOYMENT',
                },
            },
            LoadBalancerInfo={
                'targetGroupPairInfoList': [
                    {
                        'targetGroups': [
                            {
                                'name': main_target_group.Name
                            },
                            {
                                'name': deployments_target_group.Name
                            },
                        ],
                        'prodTrafficRoute': {
                            'listenerArns': [
                                Ref(main_listener)
                            ]
                        },
                        'testTrafficRoute': {
                            'listenerArns': [
                                Ref(deployments_listener)
                            ]
                        }
                    },
                ]
            },
            EcsServices=[
                {
                    'serviceName': ecs_service_name,
                    'clusterName': ecs_cluster_name
                },
            ]
        )

        self.pipeline = Pipeline(
            prefix + 'FargateEcsPipeline',
            ArtifactStore=ArtifactStore(
                Location=artifact_builds_s3,
                Type='S3'
            ),
            Name=prefix + 'FargateEcsPipeline',
            RoleArn=GetAtt(self.pipeline_role, 'Arn'),
            Stages=[
                Stages(
                    Name='SourceStage',
                    Actions=[
                        Actions(
                            Name='SourceEcrAction',
                            ActionTypeId=ActionTypeId(
                                Category='Source',
                                Owner='AWS',
                                Version='1',
                                Provider='ECR'
                            ),
                            OutputArtifacts=[
                                OutputArtifacts(
                                    Name='EcsImage'
                                )
                            ],
                            Configuration={
                                'RepositoryName': self.ecr_repository.RepositoryName
                            },
                            RunOrder='1'
                        ),
                        Actions(
                            Name='SourceCodeCommitAction',
                            ActionTypeId=ActionTypeId(
                                Category='Source',
                                Owner='AWS',
                                Version='1',
                                Provider='CodeCommit'
                            ),
                            OutputArtifacts=[
                                OutputArtifacts(
                                    Name='EcsConfig'
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
                    Name='DeployStage',
                    Actions=[
                        Actions(
                            Name='DeployAction',
                            ActionTypeId=ActionTypeId(
                                Category='Deploy',
                                Owner='AWS',
                                Version='1',
                                Provider='CodeDeployToECS'
                            ),
                            InputArtifacts=[
                                InputArtifacts(
                                    Name='EcsImage'
                                ),
                                InputArtifacts(
                                    Name='EcsConfig'
                                )
                            ],
                            Configuration={
                                "TaskDefinitionTemplateArtifact": "EcsConfig",
                                "AppSpecTemplateArtifact": "EcsConfig",

                                "TaskDefinitionTemplatePath": "taskdef.json",
                                "AppSpecTemplatePath": "appspec.yaml",

                                "ApplicationName": self.application.ApplicationName,
                                "DeploymentGroupName": self.deployment_group.DeploymentGroupName,

                                "Image1ArtifactName": "EcsImage",
                                "Image1ContainerName": "IMAGE1_NAME"
                            },
                            RunOrder='1'
                        )
                    ]
                )
            ]
        )

    def add(self, template: Template):
        template.add_resource(self.git_repository)
        template.add_resource(self.ecr_repository)
        template.add_resource(self.deployment_group_role)
        template.add_resource(self.pipeline_role)
        template.add_resource(self.application)
        template.add_resource(self.deployment_group)
        template.add_resource(self.pipeline)
