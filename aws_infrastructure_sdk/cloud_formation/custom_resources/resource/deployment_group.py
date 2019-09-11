from troposphere import AWSObject


class CustomDeploymentGroup(AWSObject):
    resource_type = "Custom::DeploymentGroup"

    props = {
        'ServiceToken': (str, True),
        'ApplicationName': (str, True),
        'DeploymentGroupName': (str, True),
        'DeploymentConfigName': (str, False),
        'Ec2TagFilters': ([dict], False),
        'OnPremisesInstanceTagFilters': ([dict], False),
        'AutoScalingGroups': ([str], False),
        'ServiceRoleArn': (str, True),
        'TriggerConfigurations': ([dict], False),
        'AlarmConfiguration': (dict, False),
        'AutoRollbackConfiguration': (dict, False),
        'DeploymentStyle': (dict, False),
        'BlueGreenDeploymentConfiguration': (dict, False),
        'LoadBalancerInfo': (dict, False),
        'Ec2TagSet': (dict, False),
        'EcsServices': ([dict], False),
        'OnPremisesTagSet': (dict, False),
        'Tags': ([dict], False)
    }
