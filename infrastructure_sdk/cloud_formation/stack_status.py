from botocore.exceptions import ClientError
from infrastructure_sdk.cloud_formation.abstract_stack_action import AbstractStackAction


class StackStatus(AbstractStackAction):
    def __init__(self, cf_stack_name: str):
        super().__init__(cf_stack_name)

    def status(self) -> str:
        """
        Checks what is the current status of the default stack.
        """
        self.get_logger().info('Getting stack {} status...'.format(self.cf_stack_name))

        try:
            response = self.cf_client.describe_stacks(StackName=self.cf_stack_name)
            return response['Stacks'][0]['StackStatus']
        except ClientError as ex:
            self.get_logger().error('Can not check stack status. Reason: {}'.format(repr(ex)))
            raise
