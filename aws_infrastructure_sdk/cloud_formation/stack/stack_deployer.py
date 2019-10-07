from typing import Any, Dict, List
from aws_infrastructure_sdk.cloud_formation.stack.abstract_stack_action import AbstractStackAction
from aws_infrastructure_sdk.s3.s3_bucket_creator import S3BucketCreator
from aws_infrastructure_sdk.s3.s3_uploader import S3Uploader


class StackDeployer(AbstractStackAction):
    """
    Cloud-formation stack deployment class.
    """
    def __init__(self, cf_stack_name: str, region: str):
        """
        Constructor.

        :param cf_stack_name: The name of cloud-formation stack.
        """
        super().__init__(cf_stack_name)

        self.region = region

    def deploy(self, cf_bucket_name: str, template: str, parameters: List[Dict[str, Any]]) -> None:
        """
        Updates or creates cloud-formation stack.

        :param cf_bucket_name: The name of the S3 bucket where a cloud-formation template should be uploaded.
        :param template: Generated cloud-formation template.
        :param parameters: Parameters for the template.

        :return: No return.
        """
        self.get_logger().info('Deploying stack {}...'.format(self.cf_stack_name))
        self.get_logger().info('Uploading cloudformation template to S3...')

        S3BucketCreator(cf_bucket_name, self.region).create()
        s3_url = S3Uploader(cf_bucket_name).upload_bytes(template.encode('utf-8'))

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
