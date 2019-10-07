from typing import Union
from aws_cf_custom_resources.deployment_group.resource import CustomDeploymentGroup
from aws_cf_custom_resources.deployment_group.service import DeploymentGroupService
from aws_cf_custom_resources.ecs_service.resource import CustomEcsService
from aws_cf_custom_resources.git_commit.resource import CustomGitCommit
from aws_cf_custom_resources.git_commit.service import GitCommitService
from troposphere.ecs import Service, Cluster
from troposphere.s3 import Bucket
from aws_infrastructure_sdk.cloud_formation.types import AwsRef
from troposphere.codecommit import Repository as GitRepository
from troposphere.ecr import Repository as EcrRepository
from troposphere.codedeploy import Application
from troposphere.elasticloadbalancingv2 import TargetGroup, Listener
from troposphere.iam import Role, Policy
from troposphere import Template, GetAtt, Ref, Output, Join
from troposphere.codepipeline import *


class EcsPipeline:
    """
    Class which creates infrastructure for CI/CD Blue/Green Ecs Fargate deployment.
    """
    def __init__(
            self,
            prefix: str,
            aws_account_id: str,
            aws_region: str,
            main_target_group: TargetGroup,
            deployments_target_group: TargetGroup,
            main_listener: Listener,
            deployments_listener: Listener,
            ecs_service: Union[CustomEcsService, Service],
            ecs_cluster: Cluster,
            artifact_builds_s3: Bucket,
            task_def: AwsRef,
            app_spec: AwsRef,
    ):
        """
        Constructor.

        :param prefix: A prefix for newly created resources.
        :param aws_account_id: An account id under which a CF stack is running.
        :param aws_region: Region in which the CF stack is running.
        :param main_target_group: A target group to which a loadbalancer is forwarding a received production traffic.
        :param deployments_target_group: A target group to which a loadbalancer is forwarding a received test traffic.
        :param main_listener: A listener which receives incoming traffic and forwards it to a target group.
        :param deployments_listener: A listener which receives incoming traffic and forwards it to a target group.
        This listener is used for blue/green deployment.
        :param ecs_service: Ecs service to which create this pipeline.
        :param ecs_cluster: ECS cluster in which the ECS service is.
        :param artifact_builds_s3: A S3 bucket to which built artifacts are written.
        :param task_def: Task definition object defining the parameters for a newly deployed container.
        :param app_spec: App specification object defining the ecs service modifications.
        """
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
                            'ecs-tasks.amazonaws.com',
                            'codedeploy.amazonaws.com',
                        ]
                    }
                }
            ]},
        )

        # TODO needs permissions fixing.
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
            RepositoryName=prefix.lower() + '_config'
        )

        # Commit configuration files to a git repository from which a code-pipeline will read later.
        self.commit = CustomGitCommit(
            prefix + 'FargateEcsDeploymentConfig',
            ServiceToken=GitCommitService().service_token(),
            RepositoryName=self.git_repository.RepositoryName,
            BranchName='master',
            CommitMessage='Initial appspec and taskdef files.',
            PutFiles=[
                {
                    'filePath': 'taskdef.json',
                    'fileMode': 'NORMAL',
                    'fileContent': task_def,
                }, {
                    'filePath': 'appspec.yaml',
                    'fileMode': 'NORMAL',
                    'fileContent': app_spec,
                }
            ],
            DependsOn=[self.git_repository.title]
        )

        self.ecr_repository = EcrRepository(
            prefix + 'FargateEcsEcrRepository',
            RepositoryName=prefix.lower()
        )

        self.ecr_repository_output = Output(
            prefix + 'FargateEcsEcrOutput',
            Description='Ecr endpoint to tag/push/pull docker images.',
            Value=Join(delimiter='', values=[
                f'{aws_account_id}.dkr.ecr.{aws_region}.amazonaws.com/',
                Ref(self.ecr_repository),
                f':latest',
            ])
        )

        self.application = Application(
            prefix + 'FargateEcsCodeDeployApplication',
            ApplicationName=prefix + 'FargateEcsCodeDeployApplication',
            ComputePlatform='ECS'
        )

        self.deployment_group = CustomDeploymentGroup(
            prefix + 'FargateEcsDeploymentGroup',
            ServiceToken=DeploymentGroupService().service_token(),
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
                    'serviceName': ecs_service.ServiceName,
                    'clusterName': ecs_cluster.ClusterName
                },
            ],
            DependsOn=[
                ecs_service.title,
            ]
        )

        # Create a pipeline which deploys from ECR to ECS.
        self.pipeline = Pipeline(
            prefix + 'FargateEcsPipeline',
            ArtifactStore=ArtifactStore(
                Location=artifact_builds_s3.BucketName,
                Type='S3'
            ),
            Name=prefix + 'FargateEcsPipeline',
            RoleArn=GetAtt(self.pipeline_role, 'Arn'),
            Stages=[
                Stages(
                    Name='SourceStage',
                    Actions=[
                        # Source the image from ECR.
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
                        # Source configuration from git repository.
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
                        # Initiate the deployment.
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
            ],
            # The pipeline can not be created until applications, deployment groups, git repositories and ecs
            # services are created.
            DependsOn=[
                artifact_builds_s3.title,
                self.application.title,
                self.deployment_group.title,
                self.git_repository.title,
                self.ecr_repository.title,
            ]
        )

    def add(self, template: Template):
        """
        Adds all created resources to a template.

        :param template: Template to which resources should be added.

        :return: No return.
        """
        template.add_resource(self.commit)
        template.add_resource(self.git_repository)
        template.add_resource(self.ecr_repository)
        template.add_resource(self.deployment_group_role)
        template.add_resource(self.pipeline_role)
        template.add_resource(self.application)
        template.add_resource(self.deployment_group)
        template.add_resource(self.pipeline)

        template.add_output(self.ecr_repository_output)
