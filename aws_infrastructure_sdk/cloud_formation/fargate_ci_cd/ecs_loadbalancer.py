from typing import List, Optional
from troposphere.certificatemanager import Certificate
from troposphere.ec2 import SecurityGroup, Subnet, VPC
from troposphere.elasticloadbalancingv2 import TargetGroup, LoadBalancer, Listener, Action, RedirectConfig, \
    Certificate as LBCertificate, Matcher
from troposphere import Template, Ref, Output, GetAtt


class Loadbalancing:
    """
    Class which creates a loadbalancer for ecs.
    """
    TARGET_GROUP_PORT = 80
    LISTENER_HTTP_PORT_1 = 80
    LISTENER_HTTPS_PORT_1 = 443
    LISTENER_HTTP_PORT_2 = 8000
    LISTENER_HTTPS_PORT_2 = 44300

    def __init__(
            self,
            prefix: str,
            lb_security_groups: List[SecurityGroup],
            subnets: List[Subnet],
            vpc: VPC,
            desired_domain_name: str,
            healthy_http_codes: Optional[List[int]] = None
    ):
        """
        Constructor.

        :param prefix: A prefix for resource names.
        :param lb_security_groups: Security groups to attach to a loadbalancer. NOTE! when passing loadbalancer
        security groups - make sure the loadbalancer can communicate through ci/cd blue/green deployments
        opened ports. Usually they are 8000 and 44300.
        :param subnets: Subnets in which loadbalancer can exist.
        :param vpc: Virtual private cloud in which target groups and a loadbalancer exist.
        :param desired_domain_name: Domain name for using https.
        :param healthy_http_codes: The deployed instance is constantly pinged to determine if it is available
        (healthy) or not. Specify a list of http codes that your service can return and should be treated as healthy.
        """
        # By default a healthy http code is considered to be 200.
        healthy_http_codes = healthy_http_codes or [200]

        # If your service's task definition uses the awsvpc network mode
        # (which is required for the Fargate launch type), you must choose ip as the target type,
        # not instance, when creating your target groups because
        # tasks that use the awsvpc network mode are associated with an elastic network interface,
        # not an Amazon EC2 instance.
        self.target_type = 'ip'

        # Certificate so a loadbalancer could communicate via HTTPS.
        self.certificate = Certificate(
            prefix + 'FargateEcsCertificate',
            DomainName=desired_domain_name,
            ValidationMethod='DNS',
        )

        # A main target group to which a loadbalancer forwards a HTTP traffic.
        # This is the main group with which our ecs container is associated.
        self.target_group_1_http = TargetGroup(
            prefix + 'FargateEcsTargetGroup1',
            Name=prefix + 'FargateEcsTargetGroup1',
            Matcher=Matcher(
                HttpCode=','.join([str(code) for code in healthy_http_codes])
            ),
            Port=self.TARGET_GROUP_PORT,
            Protocol='HTTP',
            VpcId=Ref(vpc),
            TargetType=self.target_type
        )

        # Second target group is usd for Blue/Green deployments. A new container (that should be deployed)
        # is associated with the second target group.
        self.target_group_2_http = TargetGroup(
            prefix + 'FargateEcsTargetGroup2',
            Name=prefix + 'FargateEcsTargetGroup2',
            Matcher=Matcher(
                HttpCode=','.join([str(code) for code in healthy_http_codes])
            ),
            Port=self.TARGET_GROUP_PORT,
            Protocol='HTTP',
            VpcId=Ref(vpc),
            TargetType=self.target_type
        )

        self.load_balancer = LoadBalancer(
            prefix + 'FargateEcsLoadBalancer',
            Subnets=[Ref(sub) for sub in subnets],
            SecurityGroups=[Ref(group) for group in lb_security_groups],
            Name=prefix + 'FargateEcsLoadBalancer',
            Scheme='internet-facing',
        )

        self.load_balancer_output = Output(
            prefix + 'FargateEcsLoadBalancerUrl',
            Description='The endpoint url of a loadbalancer.',
            Value=GetAtt(self.load_balancer, 'DNSName')
        )

        # Listener that listens to HTTP incoming traffic and redirects to other HTTPS listener.
        self.listener_http_1 = Listener(
            prefix + 'FargateEcsHttpListener1',
            Port=self.LISTENER_HTTP_PORT_1,
            Protocol='HTTP',
            LoadBalancerArn=Ref(self.load_balancer),
            DefaultActions=[
                # Redirect to https.
                Action(
                    Type='redirect',
                    RedirectConfig=RedirectConfig(
                        Host='#{host}',
                        Path='/#{path}',
                        Port=str(self.LISTENER_HTTPS_PORT_1),
                        Query='#{query}',
                        StatusCode='HTTP_301',
                        Protocol='HTTPS'
                    )
                )
            ]
        )

        # Listener that listens to HTTPS traffic and forwards to a target group.
        self.listener_https_1 = Listener(
            prefix + 'FargateEcsHttpsListener1',
            Certificates=[LBCertificate(
                CertificateArn=Ref(self.certificate)
            )],
            Port=self.LISTENER_HTTPS_PORT_1,
            Protocol='HTTPS',
            LoadBalancerArn=Ref(self.load_balancer),
            DefaultActions=[
                Action(
                    Type='forward',
                    TargetGroupArn=Ref(self.target_group_1_http)
                )
            ]
        )

        # Second listener is usd for Blue/Green deployments (testing new instance). Test HTTP traffic is
        # redirected to test HTTPS traffic.
        self.listener_http_2 = Listener(
            prefix + 'FargateEcsHttpListener2',
            Port=self.LISTENER_HTTP_PORT_2,
            Protocol='HTTP',
            LoadBalancerArn=Ref(self.load_balancer),
            DefaultActions=[
                # Redirect to https.
                Action(
                    Type='redirect',
                    RedirectConfig=RedirectConfig(
                        Host='#{host}',
                        Path='/#{path}',
                        Port=str(self.LISTENER_HTTPS_PORT_2),
                        Query='#{query}',
                        StatusCode='HTTP_301',
                        Protocol='HTTPS'
                    )
                )
            ]
        )

        # Listener that listens to test HTTP traffic and forwards to a secondary target group (new container).
        self.listener_https_2 = Listener(
            prefix + 'FargateEcsHttpsListener2',
            Certificates=[LBCertificate(
                CertificateArn=Ref(self.certificate)
            )],
            Port=self.LISTENER_HTTPS_PORT_2,
            Protocol='HTTPS',
            LoadBalancerArn=Ref(self.load_balancer),
            DefaultActions=[
                Action(
                    Type='forward',
                    TargetGroupArn=Ref(self.target_group_2_http)
                )
            ]
        )

    def add(self, template: Template):
        """
        Adds all created resources to a template.

        :param template: Template to which resources should be added.

        :return: No return.
        """
        template.add_resource(self.certificate)

        template.add_resource(self.target_group_1_http)
        template.add_resource(self.target_group_2_http)

        template.add_resource(self.listener_http_1)
        template.add_resource(self.listener_https_1)
        template.add_resource(self.listener_http_2)
        template.add_resource(self.listener_https_2)

        template.add_resource(self.load_balancer)

        template.add_output(self.load_balancer_output)
