from typing import List
from troposphere.ec2 import SecurityGroup, Subnet, VPC
from troposphere.elasticloadbalancingv2 import TargetGroup, LoadBalancer, Listener, Action
from troposphere import Template, Ref


class Loadbalancing:
    def __init__(self, prefix: str, lb_security_groups: List[SecurityGroup], subnets: List[Subnet], vpc: VPC):
        """
        Constructor.

        :param prefix: A prefix for resource names.
        :param lb_security_groups: Security groups to attach to a loadbalancer.
        :param subnets: Subnets in which loadbalancer can exist.
        :param vpc: Virtual private cloud in which target groups and a loadbalancer would exist.
        """
        self.target_group_port_http = 80
        # If your service's task definition uses the awsvpc network mode
        # (which is required for the Fargate launch type), you must choose ip as the target type,
        # not instance, when creating your target groups because
        # tasks that use the awsvpc network mode are associated with an elastic network interface,
        # not an Amazon EC2 instance.
        self.target_type = 'ip'

        self.target_group_1_http = TargetGroup(
            prefix + 'FargateEcsTargetGroup1',
            Name=prefix + 'FargateEcsTargetGroup1',
            Port=self.target_group_port_http,
            Protocol='HTTP',
            VpcId=Ref(vpc),
            TargetType=self.target_type
        )

        # Second target group is usd for Blue/Green deployments.
        self.target_group_2_http = TargetGroup(
            prefix + 'FargateEcsTargetGroup2',
            Name=prefix + 'FargateEcsTargetGroup2',
            Port=self.target_group_port_http,
            Protocol='HTTP',
            VpcId=Ref(vpc),
            TargetType=self.target_type
        )

        self.load_balancer = LoadBalancer(
            prefix + 'FargateEcsLoadBalancer',
            Subnets=[Ref(subnet) for subnet in subnets],
            SecurityGroups=[Ref(lb_security_groups)],
            Name=prefix + 'FargateEcsLoadBalancer',
            Scheme='internet-facing',
        )

        self.listener_port_1 = 80
        self.listener_http_1 = Listener(
            prefix + 'FargateEcsHttpListener1',
            Port=self.listener_port_1,
            Protocol='HTTP',
            LoadBalancerArn=Ref(self.load_balancer),
            DefaultActions=[
                Action(
                    Type='forward',
                    TargetGroupArn=Ref(self.target_group_1_http)
                )
            ]
        )

        # Second listener is usd for Blue/Green deployments (testing new instance).
        self.listener_port_2 = 8080
        self.listener_http_2 = Listener(
            prefix + 'FargateEcsHttpListener2',
            Port=self.listener_port_2,
            Protocol='HTTP',
            LoadBalancerArn=Ref(self.load_balancer),
            DefaultActions=[
                Action(
                    Type='forward',
                    TargetGroupArn=Ref(self.target_group_2_http)
                )
            ]
        )

    def add(self, template: Template):
        template.add_resource(self.target_group_1_http)
        template.add_resource(self.target_group_2_http)
        template.add_resource(self.load_balancer)
        template.add_resource(self.listener_http_1)
        template.add_resource(self.listener_http_2)
