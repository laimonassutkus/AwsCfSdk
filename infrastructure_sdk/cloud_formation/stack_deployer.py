from typing import Any, Dict, List
from infrastructure_sdk.cloud_formation.abstract_stack_action import AbstractStackAction
from infrastructure_sdk.s3.uploader import Uploader


class StackDeployer(AbstractStackAction):
    def __init__(self, cf_stack_name: str):
        super().__init__(cf_stack_name)

    def deploy(self, cf_bucket_name: str, template: str, parameters: List[Dict[str, Any]]):
        """
        Updates or creates a stack.
        """
        self.get_logger().info('Deploying stack {}...'.format(self.cf_stack_name))
        self.get_logger().info('Uploading cloudformation template to S3...')

        s3_url = Uploader(cf_bucket_name).upload_bytes(template.encode('utf-8'))

        kwargs = {
            'StackName': self.cf_stack_name,
            'TemplateURL': s3_url,
            'Capabilities': [
                'CAPABILITY_IAM',
            ],
            'Parameters': parameters
        }

        try:
            response = self.cf_client.create_stack(**kwargs)
        except self.cf_client.exceptions.AlreadyExistsException:
            response = self.cf_client.update_stack(**kwargs)

        self.get_logger().info('Done! Stack response: {}'.format(response))
