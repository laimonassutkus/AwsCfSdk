import boto3

from typing import Any, Dict

client = boto3.client('codedeploy')


class Group:
    @staticmethod
    def create(**kwargs) -> Dict[str, Any]:
        kwargs = dict(
            applicationName=kwargs.get('applicationName'),
            deploymentGroupName=kwargs.get('deploymentGroupName'),
            deploymentConfigName=kwargs.get('deploymentConfigName'),
            ec2TagFilters=kwargs.get('ec2TagFilters'),
            onPremisesInstanceTagFilters=kwargs.get('onPremisesInstanceTagFilters'),
            autoScalingGroups=kwargs.get('autoScalingGroups'),
            serviceRoleArn=kwargs.get('serviceRoleArn'),
            triggerConfigurations=kwargs.get('triggerConfigurations'),
            alarmConfiguration=kwargs.get('alarmConfiguration'),
            autoRollbackConfiguration=kwargs.get('autoRollbackConfiguration'),
            deploymentStyle=kwargs.get('deploymentStyle'),
            blueGreenDeploymentConfiguration=kwargs.get('blueGreenDeploymentConfiguration'),
            loadBalancerInfo=kwargs.get('loadBalancerInfo'),
            ec2TagSet=kwargs.get('ec2TagSet'),
            ecsServices=kwargs.get('ecsServices'),
            onPremisesTagSet=kwargs.get('onPremisesTagSet'),
            tags=kwargs.get('tags')
        )

        kwargs = {key: value for key, value in kwargs.items() if key and value}
        return client.create_deployment_group(**kwargs)

    @staticmethod
    def update(**kwargs: Dict[str, Any]) -> Dict[str, Any]:
        kwargs = dict(
            applicationName=kwargs.get('applicationName'),
            currentDeploymentGroupName=kwargs.get('deploymentGroupName'),
            newDeploymentGroupName=kwargs.get('newDeploymentGroupName'),
            deploymentConfigName=kwargs.get('deploymentConfigName'),
            ec2TagFilters=kwargs.get('ec2TagFilters'),
            onPremisesInstanceTagFilters=kwargs.get('onPremisesInstanceTagFilters'),
            autoScalingGroups=kwargs.get('autoScalingGroups'),
            serviceRoleArn=kwargs.get('serviceRoleArn'),
            triggerConfigurations=kwargs.get('triggerConfigurations'),
            alarmConfiguration=kwargs.get('alarmConfiguration'),
            autoRollbackConfiguration=kwargs.get('autoRollbackConfiguration'),
            deploymentStyle=kwargs.get('deploymentStyle'),
            blueGreenDeploymentConfiguration=kwargs.get('blueGreenDeploymentConfiguration'),
            loadBalancerInfo=kwargs.get('loadBalancerInfo'),
            ec2TagSet=kwargs.get('ec2TagSet'),
            ecsServices=kwargs.get('ecsServices'),
            onPremisesTagSet=kwargs.get('onPremisesTagSet'),
        )

        kwargs = {key: value for key, value in kwargs.items() if key and value}
        return client.update_deployment_group(**kwargs)

    @staticmethod
    def delete(**kwargs: Dict[str, Any]) -> Dict[str, Any]:
        kwargs = dict(
            applicationName=kwargs.get('applicationName'),
            deploymentGroupName=kwargs.get('deploymentGroupName'),
        )

        kwargs = {key: value for key, value in kwargs.items() if key and value}
        return client.delete_deployment_group(**kwargs)
