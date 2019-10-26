from typing import List, Dict, Optional
from troposphere import Template
from troposphere.ec2 import SecurityGroup, Subnet, VPC
from troposphere.s3 import Bucket
from aws_infrastructure_sdk.cloud_formation.fargate_ci_cd.ecs_autoscaling import Autoscaling
from aws_infrastructure_sdk.cloud_formation.fargate_ci_cd.ecs_loadbalancer import Loadbalancing
from aws_infrastructure_sdk.cloud_formation.fargate_ci_cd.ecs_main import Ecs
from aws_infrastructure_sdk.cloud_formation.fargate_ci_cd.ecs_pipeline import EcsPipeline
from aws_infrastructure_sdk.cloud_formation.types import AwsRef


class EcsParams:
    """
    Parameters class which specifies deployed container and ecs parameters such as name, port, etc.
    """
    def __init__(
            self,
            container_name: str,
            container_cpu: str,
            container_ram: str,
            container_port: int,
            container_environment: Dict[str, AwsRef],
            ecs_security_groups: List[SecurityGroup],
            ecs_subnets: List[Subnet]
    ) -> None:
        """
        Constructor.

        :param container_name: The name that will be given to a newly deployed container.
        :param container_cpu: Cpu points for the deployed container. 1 CPU = 1024 Cpu units.
        :param container_ram: Memory for the deployed container. 1 GB Ram = 1024 units.
        :param container_port: An open container port through which a loadbalancer can communicate.
        :param container_environment: Environment that will be passed to a running container.
        :param ecs_security_groups: Security groups for ecs service in which containers are placed.
        :param ecs_subnets: Subnets to which new containers will be deployed.
        """
        self.container_name = container_name
        self.container_cpu = container_cpu
        self.container_ram = container_ram
        self.container_port = container_port
        self.container_environment = container_environment
        self.ecs_security_groups = ecs_security_groups
        self.ecs_subnets = ecs_subnets


class LoadBalancerParams():
    def __init__(
            self,
            subnets: List[Subnet],
            security_groups: List[SecurityGroup],
            dns: str,
            healthy_http_codes: Optional[List[int]] = None
    ):
        """
        Constructor.

        :param subnet: Subnets in which a newly created loadbalancer can operate.
        :param dns: A domain name for a loadbalancer. E.g. myweb.com. This is used to issue a new
        certificate in order a loadbalancer can use HTTPS connections.
        :param healthy_http_codes: The deployed instance is constantly pinged to determine if it is available
        (healthy) or not. Specify a list of http codes that your service can return and should be treated as healthy.
        """
        self.dns = dns
        self.security_groups = security_groups
        self.lb_subnets = subnets
        self.healthy_http_codes = healthy_http_codes


class PipelineParams:
    """
    Parameters class which specifies various parameters for ci/cd pipeline.
    """
    def __init__(self, artifact_builds_bucket: Bucket):
        """
        Constructor.

        :param artifact_builds_bucket: An artifacts bucket which will be used by a ci/cd pipeline to write
        and read build/source artifacts.
        """
        self.artifact_builds_bucket = artifact_builds_bucket


class Main:
    """
    Main class which provisions whole infrastructure regarding:
        1. ECS Fargate,
        2. Autoscaling,
        3. Loadbalancing,
        4. Pipeline CI/CD.

    Known pitfalls:
        1. Cloudformation updates a deployment group or an ecs service by deleting it and creating a new one. However
        "create" action is never called (probably a bug in cloudformation dealing with custom resources functionality).
        After an update a deployment group or an ecs service are deleted an no longer exist. To fix that - tear down
        the whole main ecs fargate ci/cd stack and rerun it.
    """
    def __init__(
            self,
            prefix: str,
            region: str,
            account_id: str,
            vpc: VPC,
            lb_params: LoadBalancerParams,
            ecs_params: EcsParams,
            pipeline_params: PipelineParams,
    ) -> None:
        """
        Constructor.

        :param prefix: The prefix for all newly created resources. E.g. Wordpress.
        :param region: The region where resources and the stack are deployed.
        :param account_id: The id of the account which executes this stack.
        :param vpc: Virtual private cloud (VPC).
        :param lb_params: Loadbalancer parameters.
        :param ecs_params: Compute power parameters for newly deployed container.
        :param pipeline_params: Parameters for a ci/cd pipeline.
        """
        # Create a loadbalancer to which an ecs service will attach.
        self.load_balancing = Loadbalancing(
            prefix=prefix,
            subnets=lb_params.lb_subnets,
            lb_security_groups=lb_params.security_groups,
            vpc=vpc,
            desired_domain_name=lb_params.dns,
            healthy_http_codes=lb_params.healthy_http_codes
        )

        # Create main fargate ecs service.
        self.ecs = Ecs(
            prefix=prefix,
            aws_region=region,
            environment=ecs_params.container_environment,
            cpu=ecs_params.container_cpu,
            ram=ecs_params.container_ram,
            container_name=ecs_params.container_name,
            container_port=ecs_params.container_port,
            target_group=self.load_balancing.target_group_1_http,
            security_groups=ecs_params.ecs_security_groups,
            subnets=ecs_params.ecs_subnets,
            # Ecs can not be created until a loadbalancer is created.
            depends_on_loadbalancers=[self.load_balancing.load_balancer],
            # Ecs can not be created until target groups are created.
            depends_on_target_groups=[
                self.load_balancing.target_group_1_http,
                self.load_balancing.target_group_2_http
            ],
            # Ecs can not be created until listeners are associated with a loadbalancer and target groups.
            depends_on_listeners=[
                self.load_balancing.listener_http_1,
                self.load_balancing.listener_http_2,
                self.load_balancing.listener_https_1,
                self.load_balancing.listener_https_2,
            ]
        )

        # Create autoscaling for an ecs service.
        self.autoscaling = Autoscaling(
            prefix=prefix,
            service_name=self.ecs.service.ServiceName,
            cluster_name=self.ecs.cluster.ClusterName,
            service_resource_name=self.ecs.service.title
        )

        # Finally, create a pipeline deploying from ECR to ECS with Blue/Green deployments style.
        self.pipeline = EcsPipeline(
            prefix=prefix,
            main_target_group=self.load_balancing.target_group_1_http,
            deployments_target_group=self.load_balancing.target_group_2_http,
            main_listener=self.load_balancing.listener_https_1,
            deployments_listener=self.load_balancing.listener_https_2,
            ecs_service=self.ecs.service,
            ecs_cluster=self.ecs.cluster,
            artifact_builds_s3=pipeline_params.artifact_builds_bucket,
            task_def=self.ecs.create_task_def(),
            app_spec=self.ecs.create_appspec(),
            aws_account_id=account_id,
            aws_region=region,
            # Pipeline can not be created until the ecs service itself is created.
        )

    def add(self, template: Template):
        """
        Adds all created resources to a template.

        :param template: Template to which resources should be added.

        :return: No return.
        """
        self.load_balancing.add(template)
        self.ecs.add(template)
        self.autoscaling.add(template)
        self.pipeline.add(template)
