from multiprocessing import Process
from typing import List
from aws_infrastructure_sdk.cloud_formation.custom_resources.service.abstract_custom_service import AbstractCustomService
from aws_infrastructure_sdk.lambdas.deployment.deployment_package import DeploymentPackage


class CustomResourcesBuilder:
    def __init__(self, custom_resource_services: List[AbstractCustomService]):
        self.__custom_resource_services = custom_resource_services

    def build(self, upload: bool = True):
        process_pool = []

        for resource in self.__custom_resource_services:
            p = Process(target=self.__build_single, args=(resource, upload))
            p.start()

            process_pool.append(p)

        for process in process_pool:
            process.join(600 if upload else 500)

    @staticmethod
    def __build_single(resource: AbstractCustomService, upload: bool = True):
        DeploymentPackage(
            environment='none',
            project_src_path=resource.src,
            lambda_name=resource.lambda_name,
            s3_upload_bucket=resource.cf_custom_resources_bucket,
            s3_bucket_region=resource.region,
            aws_profile=resource.aws_profile_name,
            refresh_lambda=upload
        ).deploy()
