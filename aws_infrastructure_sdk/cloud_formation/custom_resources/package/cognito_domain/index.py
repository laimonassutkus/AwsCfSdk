import botocore
import cfnresponse
import boto3
import json
import logging

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


def __create(user_pool_id: str, domain_name: str):
    client = boto3.client('cognito-idp')

    response = client.create_user_pool_domain(
        Domain=domain_name,
        UserPoolId=user_pool_id
    )

    data = json.dumps(response, default=lambda o: '<not serializable>')
    logger.info(data)


def __update(user_pool_id: str, domain_name: str):
    client = boto3.client('cognito-idp')

    response = client.update_user_pool_domain(
        Domain=domain_name,
        UserPoolId=user_pool_id
    )

    data = json.dumps(response, default=lambda o: '<not serializable>')
    logger.info(data)


def __delete(user_pool_id: str, domain_name: str):
    client = boto3.client('cognito-idp')

    try:
        response = client.delete_user_pool_domain(
            Domain=domain_name,
            UserPoolId=user_pool_id
        )

        data = json.dumps(response, default=lambda o: '<not serializable>')
        logger.info(data)
    except Exception as ex:
        logger.error(repr(ex))


def __handle(event, context):
    logger.info('Got new request. Event: {}, Context: {}'.format(event, context))

    user_pool_id = event['ResourceProperties']['UserPoolId']
    domain_name = event['ResourceProperties']['DomainName']

    if event['RequestType'] == 'Delete':
        __delete(user_pool_id, domain_name)
        return

    if event['RequestType'] == 'Create':
        __create(user_pool_id, domain_name)
        return

    if event['RequestType'] == 'Update':
        __update(user_pool_id, domain_name)
        return

    raise KeyError('Unsupported request type! Type: {}'.format(event['RequestType']))


def handler(event, context):
    try:
        __handle(event, context)
    except Exception as ex:
        __failed(event, context, {'Error': str(ex)})
        return

    __success(event, context, {'Success': True})
