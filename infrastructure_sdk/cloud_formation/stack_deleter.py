from infrastructure_sdk.cloud_formation.abstract_stack_action import AbstractStackAction


class StackDeleter(AbstractStackAction):
    def __init__(self, cf_stack_name: str):
        super().__init__(cf_stack_name)

    def delete(self):
        """
        Deletes the default stack.
        """
        self.get_logger().info('Deleting stack {}...'.format(self.cf_stack_name))
        self.cf_client.delete_stack(StackName=self.cf_stack_name)
