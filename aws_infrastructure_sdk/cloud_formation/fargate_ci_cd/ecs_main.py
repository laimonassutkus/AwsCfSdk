from typing import List, Dict
from aws_cf_custom_resources.ecs_service.resource import CustomEcsService
from aws_cf_custom_resources.ecs_service.service import EcsServiceService
from troposphere.logs import LogGroup
from aws_infrastructure_sdk.cloud_formation.types import AwsRef
from troposphere.ec2 import SecurityGroup, Subnet
from troposphere.elasticloadbalancingv2 import TargetGroup, Listener
from troposphere import Template, Ref, GetAtt, Join
from troposphere.ecs import *
from troposphere.iam import Role, Policy


class Ecs:
    """
    Class that creates ECS Fargate service.
    """
    def __init__(
            self,
            prefix: str,
            aws_region: str,
            cpu: str,
            ram: str,
            environment: Dict[str, AwsRef],
            container_name: str,
            container_port: int,
            target_group: TargetGroup,
            security_groups: List[SecurityGroup],
            subnets: List[Subnet],
            depends_on_loadbalancers: List[LoadBalancer] = [],
            depends_on_target_groups: List[TargetGroup] = [],
            depends_on_listeners: List[Listener] = []
    ) -> None:
        """
        Constructor.

        :param prefix: A prefix for newly created resources.
        :param aws_region: A region in which resources are put.
        :param cpu: Cpu points for the deployed container. 1 CPU = 1024 Cpu points.
        :param ram: Memory for the deployed container. 1 GB Ram = 1024.
        :param environment: Environment that will be passed to a running container.
        :param container_name: The name that will be given to a newly deployed container.
        :param container_port: An open container port through which a loadbalancer can communicate.
        :param target_group: A main target group to which a loadbalancer will forward traffic. Also, the newly
        created container will be associated with this group.
        :param security_groups: Container security groups restricting network traffic.
        :param subnets: Subnets in which the newly created container can be placed.
        :param depends_on_loadbalancers: Before creating ecs service, these loadbalancers must be created.
        :param depends_on_target_groups: Before creating ecs service, these target groups must be created.
        :param depends_on_listeners: Before creating ecs service, these listeners must be created.
        """
        self.prefix = prefix
        self.aws_region = aws_region
        self.environment = environment
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

        self.log_group = LogGroup(
            prefix + 'FargateEcsLogGroup',
            LogGroupName=f'/aws/ecs/fargate/{prefix}'
        )

        self.cluster = Cluster(
            prefix + 'FargateEcsCluster',
            ClusterName=prefix + 'FargateEcsCluster'
        )

        self.task = TaskDefinition(
            prefix + 'FargateEcsTaskDefinition',
            RequiresCompatibilities=['FARGATE'],
            ExecutionRoleArn=GetAtt(self.task_execution_role, 'Arn'),
            ContainerDefinitions=[
                ContainerDefinition(
                    Name=container_name,
                    # Create dummy image, since container definitions list can not be empty.
                    Image='nginx:latest',
                    # For task definitions that use the awsvpc network mode, you should only specify the containerPort.
                    # The hostPort can be left blank or it must be the same value as the containerPort.
                    PortMappings=[
                        PortMapping(
                            ContainerPort=80
                        )
                    ],
                    LogConfiguration=LogConfiguration(
                        LogDriver='awslogs',
                        Options={
                            # Use Ref to set a dependency to a log group.
                            # Or use "depends on" attribute.
                            'awslogs-group': Ref(self.log_group),
                            'awslogs-region': aws_region,
                            'awslogs-stream-prefix': prefix
                        }
                    )
                )
            ],
            Cpu=cpu,
            Memory=ram,
            # For ECS Fargate - awsvpc is the only available option.
            NetworkMode='awsvpc',
            Family=prefix.lower()
        )

        self.service = CustomEcsService(
            prefix + 'FargateEcsService',
            ServiceToken=EcsServiceService().service_token(),
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
                    'subnets': [Ref(sub) for sub in subnets],
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
        """
        Creates a task definition object which will be used for deploying new containers through a pipeline.
        The task definition object specifies parameters about newly created containers.

        :return: Task definition object.
        """
        environment_list = []

        for key, value in self.environment.items():
            join = Join(delimiter='', values=['{"name": "', key, '", "value": "', value, '"}'])
            environment_list.append(join)

        environment = Join(delimiter='\n', values=[
            '"environment": [',
            Join(delimiter=',\n', values=environment_list),
            '],'
        ])

        definition = Join(delimiter='\n', values=[
            '{',
            Join(delimiter='', values=['    "executionRoleArn": ', '"', GetAtt(self.task_execution_role, "Arn"), '"', ',']),
            '    "containerDefinitions": [',
            '        {',
            '            "name": "{}",'.format(self.container_name),
            '            "image": "<IMAGE1_NAME>",',
            '            "essential": true,',
            environment,
            # For task definitions that use the awsvpc network mode, you should only specify the containerPort.
            # The hostPort can be left blank or it must be the same value as the containerPort.
            '            "portMappings": [',
            '                {',
            '                   "containerPort": {}'.format(self.container_port),
            '                }',
            '            ],',
            '            "logConfiguration": {',
            '                "logDriver": "awslogs",',
            '                "options": {',
            '                    "awslogs-group": "{}",'.format(self.log_group.LogGroupName),
            '                    "awslogs-region": "{}",'.format(self.aws_region),
            '                    "awslogs-stream-prefix": "{}"'.format(self.prefix),
            '                }',
            '            }',
            '        }',
            '    ],',
            '    "requiresCompatibilities": [',
            '        "FARGATE"',
            '    ],',
            '    "networkMode": "awsvpc",',
            '    "cpu": "{}",'.format(self.cpu),
            '    "memory": "{}",'.format(self.ram),
            '    "family": "{}"'.format(self.prefix.lower()),
            '}'
        ])

        return definition

    def create_appspec(self) -> AwsRef:
        """
        Creates an application specification object which will be used for deploying new containers through a pipeline.
        The application specification object specifies parameters about the ECS service.

        :return: Application specification object.
        """
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
        """
        Adds all created resources to a template.

        :param template: Template to which resources should be added.

        :return: No return.
        """
        template.add_resource(self.log_group)
        template.add_resource(self.cluster)
        template.add_resource(self.task)
        template.add_resource(self.service)
        template.add_resource(self.task_execution_role)
