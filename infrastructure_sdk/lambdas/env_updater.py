import boto3
import logging

from typing import Dict, Any

logr = logging.getLogger(__name__)


class EnvUpdater:
    def __init__(self, lambda_name: str):
        self.lambda_name = lambda_name

    def update(self, env: Dict[str, Any]):
        logr.info('Updating lambda environment...')

        boto3.client('lambda').update_function_configuration(
            FunctionName=self.lambda_name,
            Environment={
                'Variables': env,
            }
        )
