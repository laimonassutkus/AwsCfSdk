from multiprocessing import Process
from typing import List
from aws_infrastructure_sdk.cloud_formation.custom_resources.config import CF_CUSTOM_BUILDS_BUCKET
from aws_infrastructure_sdk.cloud_formation.custom_resources.service.abstract_custom_service import AbstractCustomService
from aws_infrastructure_sdk.lambdas.deployment.deployment_package import DeploymentPackage


class CustomResourcesBuilder:
    def __init__(self, region: str, profile: str):
        self.region = region
        self.profile = profile

    def build(self, custom_resource_services: List[AbstractCustomService], upload: bool = True):
        process_pool = []

        for resource in custom_resource_services:
            p = Process(target=self.__build_single, args=(resource, upload))
            p.start()

            process_pool.append(p)

        for process in process_pool:
            process.join(600 if upload else 500)

    def __build_single(self, resource: AbstractCustomService, upload: bool = True):
        DeploymentPackage(
            environment='none',
            project_src_path=resource.src,
            lambda_name=resource.lambda_name,
            s3_upload_bucket=CF_CUSTOM_BUILDS_BUCKET,
            s3_bucket_region=self.region,
            aws_profile=self.profile,
            refresh_lambda=upload
        ).deploy()
