from aws_infrastructure_sdk.cloud_formation.stack.abstract_stack_action import AbstractStackAction


class StackDeleter(AbstractStackAction):
    """
    Cloud-formation stack deleter class.
    """
    def __init__(self, cf_stack_name: str):
        """
        Constructor.

        :param cf_stack_name: The name of cloud-formation stack.
        """
        super().__init__(cf_stack_name)

    def delete(self):
        """
        Deletes the cloud-formation stack.

        :return: No return.
        """
        self.get_logger().info('Deleting stack {}...'.format(self.cf_stack_name))
        self.cf_client.delete_stack(StackName=self.cf_stack_name)
