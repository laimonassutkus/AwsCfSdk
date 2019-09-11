from troposphere.ec2 import SecurityGroup
from troposphere.iam import Role, Policy
from troposphere import Template, Ref
from troposphere.ecr import Repository
from troposphere.ecs import *


class WordPressFormation:
    __instance = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = object.__new__(cls)

            cls.wordpress_repository = Repository(
                'WordpressEcrRepository',
                RepositoryName='wordpress'
            )

            cls.wordpress_cluster = Cluster(
                'WordpressCluster',
                ClusterName='WordpressCluster'
            )

            # Create a database service/task in a wordpress cluster.
            cls.wordpress_database_formation = WordPressDatabaseFormation(cls.wordpress_cluster)

            cls.wordpress_container = ContainerDefinition(
                Name='WordpressContainer',
                Image='nginx:latest',
                Environment=[
                    Environment(Name='WORDPRESS_DB_HOST', Value='wpdb:3306'),
                    Environment(Name='WORDPRESS_DB_USER', Value='wordpressuser'),
                    Environment(Name='WORDPRESS_DB_PASSWORD', Value='wordpressuserpassword'),
                    Environment(Name='WORDPRESS_DB_NAME', Value='wpdb'),
                ],
                PortMappings=[
                    PortMapping(
                        ContainerPort=80
                    )
                ]
            )

            # Automatically load-balance the wordpress container.
            cls.wordpress_loadbalancer_formation = WordPressLoadBalancerFormation()

            cls.wordpress_task = TaskDefinition(
                'WordpressTaskDefinition',
                RequiresCompatibilities=['FARGATE', 'EC2'],
                Cpu='256',
                Memory='512',
                NetworkMode='awsvpc',
                ContainerDefinitions=[
                    cls.wordpress_container
                ],
                Family='wordpress'
            )

            cls.security_group = SecurityGroup(
                "WordPressServiceSecurityGroup",
                SecurityGroupIngress=[{
                    "ToPort": str(-1),
                    "FromPort": str(-1),
                    "IpProtocol": '-1',
                    "CidrIp": '0.0.0.0/0'
                }],
                SecurityGroupEgress=[{
                    "ToPort": str(-1),
                    "FromPort": str(-1),
                    "IpProtocol": '-1',
                    "CidrIp": '0.0.0.0/0'
                }],
                VpcId=Ref(VpcFormation().vpc),
                GroupDescription='A security group for wordpress ecs service.'
            )

            cls.wordpress_service_role = Role(
                'WordpressEcsServicenRole',
                Path='/',
                Policies=[Policy(
                    PolicyName='WordpressEcsServicePolicy',
                    PolicyDocument={
                        'Version': '2012-10-17',
                        'Statement': [{
                            'Effect': 'Allow',
                            'Action': 'ecs:*',
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
                                'ecs.amazonaws.com',
                            ]
                        }
                    }
                ]},
            )

            cls.wordpress_service = EcsServiceService(
                Cluster=Ref(cls.wordpress_cluster),
                ServiceName='WordpressService',
                TaskDefinition=Ref(cls.wordpress_task),
                LoadBalancers=[
                    {
                        'targetGroupArn': Ref(cls.wordpress_loadbalancer_formation.target_group_1_http),
                        'containerName': cls.wordpress_container.Name,
                        'containerPort': 80
                    },
                ],
                DesiredCount=1,
                LaunchType='FARGATE',
                NetworkConfiguration={
                    'awsvpcConfiguration': {
                        'subnets': [Ref(sub) for sub in VpcFormation().public_subnets],
                        'securityGroups': [Ref(cls.security_group)],
                        'assignPublicIp': 'ENABLED'
                    }
                },
                DeploymentController={
                    'type': 'CODE_DEPLOY'
                },
                DependsOn=[
                    # Target groups must have an associated load balancer before creating an ecs service.
                    cls.wordpress_loadbalancer_formation.load_balancer.title,
                    cls.wordpress_loadbalancer_formation.listener_http_1.title,
                    cls.wordpress_loadbalancer_formation.listener_http_2.title
                ],
            )

            # Create a wordpress service auto-scaling.
            cls.wordpress_autoscaling_formation = WordPressAutoscalingFormation(
                service_name='WordpressService',
                cluster_name='WordpressCluster',
                # Autoscaling can not be created until an ecs service is created.
                depends_on=[cls.wordpress_service.custom_resource().title]
            )

        return cls.__instance

    def add(self, template: Template):
        template.add_resource(self.security_group)
        template.add_resource(self.wordpress_repository)
        template.add_resource(self.wordpress_cluster)
        template.add_resource(self.wordpress_task)
        template.add_resource(self.wordpress_service_role)

        self.wordpress_autoscaling_formation.add(template)
        self.wordpress_loadbalancer_formation.add(template)
        self.wordpress_database_formation.add(template)

        self.wordpress_service.attach(template)
