import logging
import boto3

from typing import List

logr = logging.getLogger(__name__)


class ApiGatewayDescriber:
    def __init__(self, gateway_name: str):
        self.gateway_name = gateway_name

    def describe(self):
        logr.info(f'Getting api gateway rest api id by name {self.gateway_name}...')

        api_id = None
        api_names: List[str] = []
        for api in dict(boto3.client('apigateway').get_rest_apis().items())['items']:
            api_names.append(api['name'])

            if api['name'] == self.gateway_name:
                api_id = api['id']

        logr.info(f'Found {len(api_names)} api gateways: {api_names}.')

        assert api_id, 'Rest api id could not be found.'

        return api_id
