from troposphere.applicationautoscaling import ScalableTarget, ScalingPolicy, TargetTrackingScalingPolicyConfiguration
from troposphere.applicationautoscaling import PredefinedMetricSpecification
from troposphere.iam import Role, Policy
from troposphere import Template, Ref, GetAtt, Join


class Autoscaling:
    """
    Class that creates an ECS autoscaling.
    """
    def __init__(self, prefix: str, cluster_name: str, service_name: str, service_resource_name: str):
        """
        Container.

        :param prefix: Prefix for newly created resources.
        :param cluster_name: The name of the ECS cluster.
        :param service_name: The name of the ECS service.
        :param service_resource_name: The name of the ECS service resource to specify the dependency. Autoscaling
        can not be created until an ECS service is created.
        """
        self.autoscaling_role = Role(
            prefix + 'FargateEcsAutoscalingRole',
            Path='/',
            Policies=[Policy(
                PolicyName=prefix + 'FargateEcsAutoscalingRole',
                PolicyDocument={
                    'Version': '2012-10-17',
                    'Statement': [{
                        "Action": ["logs:*"],
                        "Resource": "arn:aws:logs:*:*:*",
                        "Effect": "Allow"
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

        self.scalable_target = ScalableTarget(
            prefix + 'FargateEcsScalableTarget',
            MinCapacity=1,
            MaxCapacity=5,
            ServiceNamespace='ecs',
            DependsOn=service_resource_name,

            # The Amazon Resource Name (ARN) of an AWS Identity and Access Management (IAM) role that
            # allows Application Auto Scaling to modify the scalable target on your behalf.
            RoleARN=GetAtt(self.autoscaling_role, 'Arn'),

            # The identifier of the resource that is associated with the scalable target.
            # This string consists of the resource type and unique identifier.
            # ECS service - The resource type is service and the unique identifier
            # is the cluster name and service name. Example: service/default/sample-webapp.
            ResourceId=Join(delimiter='/', values=[
                'service',
                cluster_name,
                service_name
            ]),
            # Read more on scalable dimensions:
            # https://docs.aws.amazon.com/autoscaling/application/APIReference
            # /API_RegisterScalableTarget.html#autoscaling-RegisterScalableTarget-request-ScalableDimension
            ScalableDimension='ecs:service:DesiredCount'
        )

        self.scaling_policy = ScalingPolicy(
            prefix + 'FargateEcsScalingPolicy',
            PolicyName=prefix + 'FargateEcsScalingPolicy',
            ScalingTargetId=Ref(self.scalable_target),
            PolicyType='TargetTrackingScaling',
            TargetTrackingScalingPolicyConfiguration=TargetTrackingScalingPolicyConfiguration(
                DisableScaleIn=False,
                TargetValue=75.0,
                PredefinedMetricSpecification=PredefinedMetricSpecification(
                    PredefinedMetricType='ECSServiceAverageCPUUtilization'
                )
            )
        )

    def add(self, template: Template):
        """
        Adds all created resources to a template.

        :param template: Template to which resources should be added.

        :return: No return.
        """
        template.add_resource(self.autoscaling_role)
        template.add_resource(self.scalable_target)
        template.add_resource(self.scaling_policy)
