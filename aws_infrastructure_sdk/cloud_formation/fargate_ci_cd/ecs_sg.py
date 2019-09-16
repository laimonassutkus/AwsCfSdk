from typing import List
from troposphere.ec2 import SecurityGroup
from troposphere import Template


class SecurityGroups:
    """
    Class which creates various security group resources.
    """
    def __init__(self, prefix, ecs_service_open_ports: List[int], load_balancer_open_ports: List[int], vpc_id: str):
        """
        Constructor.

        :param prefix: Prefix for newly created security groups. E.g. Wordpress.
        :param ecs_service_open_ports: Security group open ports for a newly deployed ecs container.
        :param load_balancer_open_ports: Security group open ports for a loadbalancer.
        :param vpc_id:
        """
        # Create a security groups config out of given open ports.
        ports = ecs_service_open_ports or [22, 80, 443, 3306]
        config = [{
            "ToPort": str(port),
            "FromPort": str(port),
            "IpProtocol": 'TCP',
            "CidrIp": '0.0.0.0/0'
        } for port in ports]

        self.ecs_security_group = SecurityGroup(
            prefix + "FargateEcsSecurityGroup",
            SecurityGroupIngress=config,
            SecurityGroupEgress=config,
            VpcId=vpc_id,
            GroupDescription='A security group for ecs service.'
        )

        # Create a security groups config out of given open ports.
        ports = load_balancer_open_ports or [22, 80, 443, 3306]
        config = [{
            "ToPort": str(port),
            "FromPort": str(port),
            "IpProtocol": 'TCP',
            "CidrIp": '0.0.0.0/0'
        } for port in ports]

        self.lb_security_group = SecurityGroup(
            prefix + "FargateEcsLoadBalancerSecurityGroup",
            SecurityGroupIngress=config,
            SecurityGroupEgress=config,
            VpcId=vpc_id,
            GroupDescription='A security group for ecs service loadbalancer.'
        )

    def add(self, template: Template):
        """
        Adds all created resources to a template.

        :param template: Template to which resources should be added.

        :return: No return.
        """
        template.add_resource(self.ecs_security_group)
        template.add_resource(self.lb_security_group)
