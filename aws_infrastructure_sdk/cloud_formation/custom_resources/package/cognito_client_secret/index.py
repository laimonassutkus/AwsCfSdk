import cfnresponse
import boto3
import botocore
import logging

from typing import Dict, Optional

logger = logging.getLogger()
logger.setLevel(logging.INFO)

logger.info(f'Version of boto3 lib: {boto3.__version__}.')
logger.info(f'Version of botocore lib: {botocore.__version__}.')


def __success(event, context, data):
    logger.info('SUCCESS: {}'.format(data))
    cfnresponse.send(event, context, cfnresponse.SUCCESS, data)


def __failed(event, context, data):
    logger.info('FAIL: {}'.format(data))
    cfnresponse.send(event, context, cfnresponse.FAILED, data)


def __create(user_pool_id: str, client_id: str) -> Optional[str]:
    client = boto3.client('cognito-idp')

    try:
        response = client.describe_user_pool_client(
            UserPoolId=user_pool_id,
            ClientId=client_id
        )

        logger.info(response)
    except Exception as ex:
        logger.error(repr(ex))
        return None

    try:
        return response['UserPoolClient']['ClientSecret']
    except KeyError as ex:
        logger.error(repr(ex))
        return None


def __update(user_pool_id: str, client_id: str) -> Optional:
    client = boto3.client('cognito-idp')

    try:
        response = client.describe_user_pool_client(
            UserPoolId=user_pool_id,
            ClientId=client_id
        )

        logger.info(response)
    except Exception as ex:
        logger.error(repr(ex))
        return None

    try:
        return response['UserPoolClient']['ClientSecret']
    except KeyError as ex:
        logger.error(repr(ex))
        return None


def __delete():
    # Since this function is used only to retrieve information,
    # no delete actions are required to be taken.
    pass


def __handle(event, context) -> Dict[str, Optional[str]]:
    logger.info('Got new request. Event: {}, Context: {}'.format(event, context))

    user_pool_id = event['ResourceProperties']['UserPoolId']
    client_id = event['ResourceProperties']['ClientId']

    if event['RequestType'] == 'Delete':
        __delete()
        return {'Secret': None}

    if event['RequestType'] == 'Create':
        secret = __create(user_pool_id, client_id)
        return {'Secret': secret}

    if event['RequestType'] == 'Update':
        secret = __update(user_pool_id, client_id)
        return {'Secret': secret}

    raise KeyError('Unsupported request type! Type: {}'.format(event['RequestType']))


def handler(event, context):
    try:
        data = __handle(event, context)
    except Exception as ex:
        __failed(event, context, {'Error': str(ex)})
        return

    __success(event, context, data)
