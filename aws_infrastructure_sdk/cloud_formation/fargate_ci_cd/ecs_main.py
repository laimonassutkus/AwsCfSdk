from typing import List
from troposphere.awslambda import Function
from troposphere.ec2 import SecurityGroup, Subnet
from troposphere.elasticloadbalancingv2 import TargetGroup, Listener
from troposphere import Template, Ref, GetAtt
from troposphere.ecr import Repository
from troposphere.ecs import *
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
            subnets: List[Subnet],
            depends_on_loadbalancers: List[LoadBalancer] = [],
            depends_on_target_groups: List[TargetGroup] = [],
            depends_on_listeners: List[Listener] = []
    ) -> None:
        self.wordpress_repository = Repository(
            prefix + 'EcrRepository',
            RepositoryName=prefix.lower()
        )

        self.cluster = Cluster(
            prefix + 'FargateEcsCluster',
            ClusterName=prefix + 'FargateEcsCluster'
        )

        self.task = TaskDefinition(
            prefix + 'FargateEcsTaskDefinition',
            RequiresCompatibilities=['FARGATE'],
            Cpu=cpu,
            Memory=ram,
            NetworkMode='awsvpc',
            ContainerDefinitions=[],
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

    def add(self, template: Template):
        template.add_resource(self.wordpress_repository)
        template.add_resource(self.cluster)
        template.add_resource(self.task)
        template.add_resource(self.service)
