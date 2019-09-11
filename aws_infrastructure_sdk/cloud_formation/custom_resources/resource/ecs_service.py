from troposphere import AWSObject
from troposphere.validators import boolean


class CustomEcsService(AWSObject):
    resource_type = "Custom::EcsService"

    props = {
        'ServiceToken': (str, True),
        'Cluster': (str, False),
        'ServiceName': (str, True),
        'TaskDefinition': (str, False),
        'LoadBalancers': ([dict], False),
        'ServiceRegistries': ([dict], False),
        'DesiredCount': (int, False),
        'LaunchType': (str, False),
        'PlatformVersion': (str, False),
        'Role': (str, False),
        'DeploymentConfiguration': (dict, False),
        'PlacementConstraints': ([dict], False),
        'PlacementStrategy': ([dict], False),
        'NetworkConfiguration': (dict, False),
        'HealthCheckGracePeriodSeconds': (int, False),
        'SchedulingStrategy': (str, False),
        'DeploymentController': (dict, False),
        'Tags': ([dict], False),
        'EnableECSManagedTags': (boolean, False),
        'PropagateTags': (str, False),
    }
