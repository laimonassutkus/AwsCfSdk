from typing import List
from troposphere.ec2 import SecurityGroup
from troposphere import Template


class SecurityGroups:
    def __init__(self, prefix, ecs_service_open_ports: List[int], load_balancer_open_ports: List[int], vpc_id: str):
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
        template.add_resource(self.ecs_security_group)
        template.add_resource(self.lb_security_group)
