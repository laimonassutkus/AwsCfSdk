from typing import List

from aws_infrastructure_sdk.cloud_formation.types import AwsRef
from troposphere.awslambda import Function
from troposphere.ec2 import SecurityGroup
from troposphere.elasticloadbalancingv2 import TargetGroup, Listener
from troposphere import Template, Ref, GetAtt, Join
from troposphere.ecs import *
from troposphere.iam import Role, Policy

from aws_infrastructure_sdk.cloud_formation.custom_resources.resource.ecs_service import CustomEcsService


class Ecs:
    def __init__(
            self,
            prefix: str,
            cpu: str,
            ram: str,
            container_name: str,
            container_port: int,
            custom_ecs_service_lambda_function: Function,
            target_group: TargetGroup,
            security_groups: List[SecurityGroup],
            subnet_ids: List[str],
            depends_on_loadbalancers: List[LoadBalancer] = [],
            depends_on_target_groups: List[TargetGroup] = [],
            depends_on_listeners: List[Listener] = []
    ) -> None:
        self.prefix = prefix
        self.cpu = cpu
        self.ram = ram
        self.container_name = container_name
        self.container_port = container_port

        self.task_execution_role = Role(
            prefix + 'FargateEcsTaskExecutionRole',
            Path='/',
            Policies=[Policy(
                PolicyName=prefix + 'FargateEcsTaskExecutionPolicy',
                PolicyDocument={
                    'Version': '2012-10-17',
                    'Statement': [{
                        'Action': [
                            "ecr:GetAuthorizationToken",
                            "ecr:BatchCheckLayerAvailability",
                            "ecr:GetDownloadUrlForLayer",
                            "ecr:BatchGetImage",
                            "logs:CreateLogStream",
                            "logs:PutLogEvents"
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
                        ]
                    }
                }
            ]},
        )

        self.cluster = Cluster(
            prefix + 'FargateEcsCluster',
            ClusterName=prefix + 'FargateEcsCluster'
        )

        self.task = TaskDefinition(
            prefix + 'FargateEcsTaskDefinition',
            RequiresCompatibilities=['FARGATE'],
            ContainerDefinitions=[
                ContainerDefinition(
                    Name=container_name,
                    # Create dummy image, since container definitions list can not be empty.
                    Image='nginx:latest',
                    PortMappings=[
                        PortMapping(
                            ContainerPort=80
                        )
                    ]
                )
            ],
            Cpu=cpu,
            Memory=ram,
            NetworkMode='awsvpc',
            Family=prefix.lower()
        )

        self.service = CustomEcsService(
            prefix + 'FargateEcsService',
            ServiceToken=GetAtt(custom_ecs_service_lambda_function, 'Arn'),
            Cluster=Ref(self.cluster),
            ServiceName=prefix + 'FargateEcsService',
            TaskDefinition=Ref(self.task),
            LoadBalancers=[
                {
                    'targetGroupArn': Ref(target_group),
                    'containerName': container_name,
                    'containerPort': container_port
                },
            ],
            DesiredCount=1,
            LaunchType='FARGATE',
            NetworkConfiguration={
                'awsvpcConfiguration': {
                    'subnets': subnet_ids,
                    'securityGroups': [Ref(sub) for sub in security_groups],
                    'assignPublicIp': 'ENABLED'
                }
            },
            DeploymentController={
                'type': 'CODE_DEPLOY'
            },
            # Target groups must have an associated load balancer before creating an ecs service.
            DependsOn=(
                    [lb.title for lb in depends_on_loadbalancers] +
                    [tg.title for tg in depends_on_target_groups] +
                    [l.title for l in depends_on_listeners]
            )
        )

    def create_task_def(self) -> AwsRef:
        definition = Join(delimiter='', values=[
            '{',
            Join(delimiter=',', values=[
                f'executionRoleArn": {GetAtt(self.task_execution_role, "Arn")},',
                str({
                    "containerDefinitions": [
                        {
                            "name": self.container_name,
                            "image": "<IMAGE1_NAME>",
                            "essential": True,
                            "portMappings": [
                                {
                                    "hostPort": self.container_port,
                                    "protocol": "tcp",
                                    "containerPort": self.container_port
                                }
                            ]
                        }
                    ],
                    "requiresCompatibilities": [
                        "FARGATE"
                    ],
                    "networkMode": "awsvpc",
                    "cpu": self.cpu,
                    "memory": self.ram,
                    "family": self.prefix.lower()
                })
            ]),
            '}'
        ])

        return definition

    def create_appspec(self) -> str:
        app_spec = (
            f'version: 0.0',
            f'Resources:',
            f'  - TargetService:',
            f'      Type: AWS::ECS::Service',
            f'      Properties:',
            f'        TaskDefinition: <TASK_DEFINITION>',
            f'        LoadBalancerInfo:',
            f'          ContainerName: "{self.container_name}"',
            f'          ContainerPort: 80',
        )

        return '\n'.join(app_spec)

    def add(self, template: Template):
        template.add_resource(self.cluster)
        template.add_resource(self.task)
        template.add_resource(self.service)
        template.add_resource(self.task_execution_role)
