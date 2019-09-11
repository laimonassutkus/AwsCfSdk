import boto3

from botocore.exceptions import ClientError
from typing import Any, Dict

client = boto3.client('ecs')


class Service:
    @staticmethod
    def create(**kwargs) -> Dict[str, Any]:
        kwargs = dict(
            cluster=kwargs.get('cluster'),
            serviceName=kwargs.get('serviceName'),
            taskDefinition=kwargs.get('taskDefinition'),
            loadBalancers=kwargs.get('loadBalancers'),
            serviceRegistries=kwargs.get('serviceRegistries'),
            desiredCount=kwargs.get('desiredCount'),
            clientToken=kwargs.get('clientToken'),
            launchType=kwargs.get('launchType'),
            platformVersion=kwargs.get('platformVersion'),
            role=kwargs.get('role'),
            deploymentConfiguration=kwargs.get('deploymentConfiguration'),
            placementConstraints=kwargs.get('placementConstraints'),
            placementStrategy=kwargs.get('placementStrategy'),
            networkConfiguration=kwargs.get('networkConfiguration'),
            healthCheckGracePeriodSeconds=kwargs.get('healthCheckGracePeriodSeconds'),
            schedulingStrategy=kwargs.get('schedulingStrategy'),
            deploymentController=kwargs.get('deploymentController'),
            tags=kwargs.get('tags'),
            enableECSManagedTags=kwargs.get('enableECSManagedTags'),
            propagateTags=kwargs.get('propagateTags'),
        )

        kwargs = {key: value for key, value in kwargs.items() if key and value}
        return client.create_service(**kwargs)

    @staticmethod
    def update(**kwargs: Dict[str, Any]) -> Dict[str, Any]:
        filtered_kwargs = dict(
            cluster=kwargs.get('cluster'),
            service=kwargs.get('serviceName'),
            desiredCount=kwargs.get('desiredCount'),
            taskDefinition=kwargs.get('taskDefinition'),
            deploymentConfiguration=kwargs.get('deploymentConfiguration'),
            networkConfiguration=kwargs.get('networkConfiguration'),
            platformVersion=kwargs.get('platformVersion'),
            forceNewDeployment=kwargs.get('forceNewDeployment'),
            healthCheckGracePeriodSeconds=kwargs.get('healthCheckGracePeriodSeconds')
        )

        try:
            filtered_kwargs = {key: value for key, value in filtered_kwargs.items() if key and value}
            return client.update_service(**filtered_kwargs)
        except ClientError as ex:
            if ex.response['Error']['Code'] == 'InvalidParameterException':
                if 'use aws codedeploy' in ex.response['Error']['Message'].lower():
                    # For services using the blue/green (CODE_DEPLOY ) deployment controller,
                    # only the desired count, deployment configuration, and health check grace period
                    # can be updated using this API. If the network configuration, platform version, or task definition
                    # need to be updated, a new AWS CodeDeploy deployment should be created.
                    filtered_kwargs = dict(
                        cluster=kwargs.get('cluster'),
                        service=kwargs.get('serviceName'),
                        desiredCount=kwargs.get('desiredCount'),
                        deploymentConfiguration=kwargs.get('deploymentConfiguration'),
                        healthCheckGracePeriodSeconds=kwargs.get('healthCheckGracePeriodSeconds'),
                    )

                    filtered_kwargs = {key: value for key, value in filtered_kwargs.items() if key and value}
                    return client.update_service(**filtered_kwargs)
            elif ex.response['Error']['Code'] == 'ServiceNotActiveException':
                # We can not update ecs service if it is inactive.
                return {'Code': 'ServiceNotActiveException'}
            elif ex.response['Error']['Code'] == 'ServiceNotFoundException':
                # If for some reason service was not found - don't update and return.
                return {'Code': 'ServiceNotFoundException'}
            raise

    @staticmethod
    def delete(**kwargs: Dict[str, Any]) -> Dict[str, Any]:
        kwargs = dict(
            cluster=kwargs.get('cluster'),
            service=kwargs.get('serviceName'),
            force=True
        )

        kwargs = {key: value for key, value in kwargs.items() if key and value}
        return client.delete_service(**kwargs)
