import boto3
import logging

from typing import Dict, Any

logr = logging.getLogger(__name__)


class LambdaEnvUpdater:
    """
    AWS Lambda environment updater.
    More on lambda:
    https://aws.amazon.com/lambda/
    """
    def __init__(self, lambda_name: str):
        """
        Constructor.

        :param lambda_name: The name of the AWS Lambda function.
        """
        self.lambda_name = lambda_name

    def update(self, env: Dict[str, Any]):
        """
        Updates lambda function's environment.

        :param env: Environment with which a lambda should be updated.

        :return: No return.
        """
        logr.info('Updating lambda environment...')

        boto3.client('lambda').update_function_configuration(
            FunctionName=self.lambda_name,
            Environment={
                'Variables': env,
            }
        )
