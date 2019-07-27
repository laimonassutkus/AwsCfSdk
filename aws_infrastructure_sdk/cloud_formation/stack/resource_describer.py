from botocore.exceptions import ClientError
from aws_infrastructure_sdk.cloud_formation.stack.abstract_stack_action import AbstractStackAction


class ResourceDescriber(AbstractStackAction):
    """
    Resources created with cloud-formation stack describer class.
    """
    def __init__(self, cf_stack_name: str):
        """
        Constructor.

        :param cf_stack_name: The name of cloud-formation stack.
        """
        super().__init__(cf_stack_name)

    def describe(self, logical_resource_id: str):
        """
        Returns physical resource id by a logical resource id.

        :param logical_resource_id: Id of the stack resource.

        :return: Physical resource id by a logical resource id.
        """
        try:
            return self.cf_client.describe_stack_resource(
                StackName=self.cf_stack_name,
                LogicalResourceId=logical_resource_id
            )['StackResourceDetail']['PhysicalResourceId']
        except ClientError:
            self.get_logger().warning('Resource with logical id {} does not exist'.format(logical_resource_id))
            raise
