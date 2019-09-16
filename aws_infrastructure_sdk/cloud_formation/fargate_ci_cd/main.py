from typing import List, Dict
from troposphere import Template
from aws_infrastructure_sdk.cloud_formation.custom_resources.service.deployment_group import DeploymentGroupService
from aws_infrastructure_sdk.cloud_formation.custom_resources.service.ecs_service import EcsServiceService
from aws_infrastructure_sdk.cloud_formation.custom_resources.service.git_commit import GitCommitService
from aws_infrastructure_sdk.cloud_formation.fargate_ci_cd.ecs_autoscaling import Autoscaling
from aws_infrastructure_sdk.cloud_formation.fargate_ci_cd.ecs_loadbalancer import Loadbalancing
from aws_infrastructure_sdk.cloud_formation.fargate_ci_cd.ecs_main import Ecs
from aws_infrastructure_sdk.cloud_formation.fargate_ci_cd.ecs_pipeline import EcsPipeline
from aws_infrastructure_sdk.cloud_formation.fargate_ci_cd.ecs_sg import SecurityGroups
from aws_infrastructure_sdk.cloud_formation.types import AwsRef


class EcsComputeParams:
    """
    Parameters class which specifies compute parameters for newly created ECS containers.
    """
    def __init__(self, cpu: str, ram: str):
        """
        Constructor.

        :param cpu: Cpu points for the deployed container. 1 CPU = 1024 Cpu points.
        :param ram: Memory for the deployed container. 1 GB Ram = 1024.
        """
        self.cpu = cpu
        self.ram = ram


class EcsContainerParams:
    """
    Parameters class which specifies deployed container parameters such as name, port, etc.
    """
    def __init__(self, container_name: str, container_port: int, environment: Dict[str, AwsRef]):
        """
        Constructor.

        :param container_name: The name that will be given to a newly deployed container.
        :param container_port: An open container port through which a loadbalancer can communicate.
        :param environment: Environment that will be passed to a running container.
        """
        self.container_name = container_name
        self.container_port = container_port
        self.environment = environment


class VpcParams:
    """
    Parameters class which specifies network parameters.
    """
    def __init__(self, vpc_id: AwsRef, lb_subnet_ids: List[AwsRef], ecs_service_subnet_ids: List[AwsRef]):
        """
        Constructor.

        :param vpc_id: VPC id in which containers, loadbalancers and other resources will be / are deployed.
        :param lb_subnet_ids: Subnet ids in which a newly created loadbalancer can operate.
        :param ecs_service_subnet_ids: Subnet ids to which new containers will be deployed.
        """
        self.vpc_id = vpc_id
        self.lb_subnet_ids = lb_subnet_ids
        self.ecs_service_subnet_ids = ecs_service_subnet_ids


class PortsParams:
    """
    Parameters class which specifies open ports for various services.
    """
    def __init__(self, ecs_service_open_ports: List[int], load_balancer_open_ports: List[int]):
        """
        Constructor.

        :param ecs_service_open_ports: Ports through which an ecs will be allowed to communicate.
        It is usually 22 (SSH), 80 (HTTP) and 443 (HTTPS).
        :param load_balancer_open_ports: Ports through which a loadbalancer will be allowed to communicate.
        It is usually 80 (HTTP) and 443 (HTTPS).
        """
        self.ecs_service_open_ports = ecs_service_open_ports
        self.load_balancer_open_ports = load_balancer_open_ports


class S3Params:
    """
    Parameters class which specifies various S3 (Simple Storage Service) parameters.
    """
    def __init__(self, artifact_builds_bucket: AwsRef):
        """
        Constructor.

        :param artifact_builds_bucket: An artifacts bucket which will be used by a ci/cd pipeline to write
        and read build/source artifacts.
        """
        self.artifact_builds_bucket = artifact_builds_bucket


class DomainParams:
    """
    Parameters class which specifies domain parameters such as dns.
    """
    def __init__(self, lb_domain_name: str):
        """
        Constructor.

        :param lb_domain_name: A domain name for a loadbalancer. E.g. myweb.com. This is used to issue a new
        certificate in order a loadbalancer can use HTTPS connections.
        """
        self.lb_domain_name = lb_domain_name


class AwsAccountParams:
    """
    Parameters associated with AWS account.
    """
    def __init__(self, account_id: str, region: str):
        """
        Constructor.

        :param account_id: The id of an account which is running this stack.
        :param region: Region in which this stack is being deployed.
        """
        self.account_id = account_id
        self.region = region


class CustomResources:
    """
    A class specifying required custom CF resources. All these custom services must be built and available
    before running the main CF template.
    """
    def __init__(
            self,
            ecs_service: EcsServiceService,
            deployment_group_service: DeploymentGroupService,
            git_commit_service: GitCommitService
    ):
        """
        Constructor.

        :param ecs_service: A custom CF ECS forming service.
        :param deployment_group_service: A custom CF Deployment Group forming service.
        :param git_commit_service: A custom CF git commit action forming service.
        """
        self.ecs_service = ecs_service
        self.deployment_group_service = deployment_group_service
        self.git_commit_service = git_commit_service


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
            aws_account_params: AwsAccountParams,
            compute_params: EcsComputeParams,
            container_params: EcsContainerParams,
            vpc_params: VpcParams,
            ports_params: PortsParams,
            s3_params: S3Params,
            custom_resources: CustomResources,
            domain_params: DomainParams
    ):
        """
        Constructor.

        :param prefix: The prefix for all newly created resources. E.g. Wordpress.
        :param aws_account_params: Parameters for aws account running this stack.
        :param compute_params: Compute power parameters for newly deployed container.
        :param container_params: Newly deployed container parameters.
        :param vpc_params: Networking parameters.
        :param ports_params: Ports parameters to open/close for resources such as a loadbalancer.
        :param s3_params: Storage parameters.
        :param custom_resources: Custom resources pool required to create/modify resources.
        :param domain_params: Domain parameters mainly used to issue certificates.
        """
        # Make sure that target group port (the port to which a loadbalancer sends incoming traffic)
        # is in an open-ports-list. This port should be open in security groups too.
        if Loadbalancing.TARGET_GROUP_PORT not in ports_params.ecs_service_open_ports:
            ports_params.ecs_service_open_ports.append(Loadbalancing.TARGET_GROUP_PORT)

        # Make sure that open ports for a loadbalancer are the right ones. If there are some missing
        # opened ports - open them.
        ports_params.load_balancer_open_ports.extend([
            Loadbalancing.LISTENER_HTTP_PORT_1,
            Loadbalancing.LISTENER_HTTP_PORT_2,
            Loadbalancing.LISTENER_HTTPS_PORT_1,
            Loadbalancing.LISTENER_HTTPS_PORT_2,
        ])
        # Filter duplicates.
        ports_params.load_balancer_open_ports = list(set(ports_params.load_balancer_open_ports))

        self.custom_resources = custom_resources

        # Create security groups out of given port parameters.
        self.security_groups = SecurityGroups(
            prefix=prefix,
            ecs_service_open_ports=ports_params.ecs_service_open_ports,
            load_balancer_open_ports=ports_params.load_balancer_open_ports,
            vpc_id=vpc_params.vpc_id
        )

        # Create a loadbalancer to which an ecs service will attach.
        self.load_balancing = Loadbalancing(
            prefix=prefix,
            subnet_ids=vpc_params.lb_subnet_ids,
            lb_security_groups=[self.security_groups.lb_security_group],
            vpc_id=vpc_params.vpc_id,
            desired_domain_name=domain_params.lb_domain_name
        )

        # Create main fargate ecs service.
        self.ecs = Ecs(
            prefix=prefix,
            environment=container_params.environment,
            cpu=compute_params.cpu,
            ram=compute_params.ram,
            container_name=container_params.container_name,
            container_port=container_params.container_port,
            custom_ecs_service_lambda_function=custom_resources.ecs_service.function(),
            target_group=self.load_balancing.target_group_1_http,
            security_groups=[self.security_groups.ecs_security_group],
            subnet_ids=vpc_params.ecs_service_subnet_ids,
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
            custom_deployment_group_lambda_function=custom_resources.deployment_group_service.function(),
            main_target_group=self.load_balancing.target_group_1_http,
            deployments_target_group=self.load_balancing.target_group_2_http,
            main_listener=self.load_balancing.listener_https_1,
            deployments_listener=self.load_balancing.listener_https_2,
            ecs_service_name=self.ecs.service.ServiceName,
            ecs_cluster_name=self.ecs.cluster.ClusterName,
            artifact_builds_s3=s3_params.artifact_builds_bucket,
            task_def=self.ecs.create_task_def(),
            app_spec=self.ecs.create_appspec(),
            custom_git_commit_lambda_function=custom_resources.git_commit_service.function(),
            aws_account_id=aws_account_params.account_id,
            aws_region=aws_account_params.region,
            # Pipeline can not be created until the ecs service itself is created.
            depends_on_ecs_service=self.ecs.service
        )

    def add(self, template: Template):
        """
        Adds all created resources to a template.

        :param template: Template to which resources should be added.

        :return: No return.
        """
        self.security_groups.add(template)
        self.load_balancing.add(template)
        self.ecs.add(template)
        self.autoscaling.add(template)
        self.pipeline.add(template)
