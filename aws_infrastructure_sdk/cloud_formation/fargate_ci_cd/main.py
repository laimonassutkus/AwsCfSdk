from typing import List
from troposphere import Template
from aws_infrastructure_sdk.cloud_formation.custom_resources.service.deployment_group import DeploymentGroupService
from aws_infrastructure_sdk.cloud_formation.custom_resources.service.ecs_service import EcsServiceService
from aws_infrastructure_sdk.cloud_formation.fargate_ci_cd.ecs_autoscaling import Autoscaling
from aws_infrastructure_sdk.cloud_formation.fargate_ci_cd.ecs_loadbalancer import Loadbalancing
from aws_infrastructure_sdk.cloud_formation.fargate_ci_cd.ecs_main import Ecs
from aws_infrastructure_sdk.cloud_formation.fargate_ci_cd.ecs_pipeline import EcsPipeline
from aws_infrastructure_sdk.cloud_formation.fargate_ci_cd.ecs_sg import SecurityGroups


class ComputeParams:
    def __init__(self, cpu: str, ram: str):
        self.cpu = cpu
        self.ram = ram


class ContainerParams:
    def __init__(self, container_name: str, container_port: int):
        self.container_name = container_name
        self.container_port = container_port


class VpcParams:
    def __init__(self, vpc_id: str, lb_subnet_ids: List[str], ecs_service_subnet_ids: List[str]):
        self.vpc_id = vpc_id
        self.lb_subnet_ids = lb_subnet_ids
        self.ecs_service_subnet_ids = ecs_service_subnet_ids


class PortsParams:
    def __init__(self, ecs_service_open_ports: List[int], load_balancer_open_ports: List[int]):
        self.ecs_service_open_ports = ecs_service_open_ports
        self.load_balancer_open_ports = load_balancer_open_ports


class S3Params:
    def __init__(self, custom_resources_bucket: str, artifact_builds_bucket: str):
        self.custom_resources_bucket = custom_resources_bucket
        self.artifact_builds_bucket = artifact_builds_bucket


class Main:
    def __init__(
            self,
            prefix: str,
            region: str,
            aws_profile_name: str,
            compute_params: ComputeParams,
            container_params: ContainerParams,
            vpc_params: VpcParams,
            ports_params: PortsParams,
            s3_params: S3Params
    ):
        custom_resource_backend_args = [s3_params.custom_resources_bucket, region, aws_profile_name]
        custom_ecs_service_resource_backend = EcsServiceService(*custom_resource_backend_args)
        custom_deployment_group_resource_backend = DeploymentGroupService(*custom_resource_backend_args)

        self.security_groups = SecurityGroups(
            prefix=prefix,
            ecs_service_open_ports=ports_params.ecs_service_open_ports,
            load_balancer_open_ports=ports_params.load_balancer_open_ports,
            vpc_id=vpc_params.vpc_id
        )

        self.load_balancing = Loadbalancing(
            prefix=prefix,
            subnet_ids=vpc_params.lb_subnet_ids,
            lb_security_groups=[self.security_groups.lb_security_group],
            vpc_id=vpc_params.vpc_id
        )

        self.ecs = Ecs(
            prefix=prefix,
            cpu=compute_params.cpu,
            ram=compute_params.ram,
            container_name=container_params.container_name,
            container_port=container_params.container_port,
            custom_ecs_service_lambda_function=custom_ecs_service_resource_backend.function(),
            target_group=self.load_balancing.target_group_1_http,
            security_groups=[self.security_groups.ecs_security_group],
            subnet_ids=vpc_params.ecs_service_subnet_ids,
            depends_on_loadbalancers=[self.load_balancing.load_balancer],
            depends_on_target_groups=[
                self.load_balancing.target_group_1_http,
                self.load_balancing.target_group_2_http
            ],
            depends_on_listeners=[
                self.load_balancing.listener_http_1,
                self.load_balancing.listener_http_2
            ]
        )

        self.autoscaling = Autoscaling(
            prefix=prefix,
            service_name=self.ecs.service.ServiceName,
            cluster_name=self.ecs.cluster.ClusterName,
            service_resource_name=self.ecs.service.title
        )

        self.pipeline = EcsPipeline(
            prefix=prefix,
            custom_deployment_group_lambda_function=custom_deployment_group_resource_backend.function(),
            main_target_group=self.load_balancing.target_group_1_http,
            deployments_target_group=self.load_balancing.target_group_2_http,
            main_listener=self.load_balancing.listener_http_1,
            deployments_listener=self.load_balancing.listener_http_2,
            ecs_service_name=self.ecs.service.ServiceName,
            ecs_cluster_name=self.ecs.cluster.ClusterName,
            artifact_builds_s3=s3_params.artifact_builds_bucket,
        )


    def add(self, template: Template):
        self.security_groups.add(template)
        self.load_balancing.add(template)
        self.ecs.add(template)
        self.autoscaling.add(template)
        self.pipeline.add(template)