from botocore.exceptions import ClientError
from infrastructure_sdk.cloud_formation.abstract_stack_action import AbstractStackAction


class ResourceDescriber(AbstractStackAction):
    def __init__(self, cf_stack_name: str):
        super().__init__(cf_stack_name)

    def describe(self, logical_resource_id: str):
        """
        Returns physical resource id by a logical resource id.
        """
        try:
            return self.cf_client.describe_stack_resource(
                StackName=self.cf_stack_name,
                LogicalResourceId=logical_resource_id
            )['StackResourceDetail']['PhysicalResourceId']
        except ClientError:
            self.get_logger().warning('Resource with logical id {} does not exist'.format(logical_resource_id))
            raise
