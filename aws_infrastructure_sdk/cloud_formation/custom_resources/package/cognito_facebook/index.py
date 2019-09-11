import cfnresponse
import boto3
import botocore
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

logger.info(f'Version of boto3 lib: {boto3.__version__}.')
logger.info(f'Version of botocore lib: {botocore.__version__}.')

client = boto3.client('cognito-idp')


def __success(event, context, data):
    logger.info('SUCCESS: {}'.format(data))
    cfnresponse.send(event, context, cfnresponse.SUCCESS, data)


def __failed(event, context, data):
    logger.info('FAIL: {}'.format(data))
    cfnresponse.send(event, context, cfnresponse.FAILED, data)


def __create(user_pool_id: str, facebook_client_id: str, facebook_client_secret: str):
    response = client.create_identity_provider(
        UserPoolId=user_pool_id,
        ProviderName='Facebook',
        ProviderType='Facebook',
        ProviderDetails={
            'client_id': facebook_client_id,
            'client_secret': facebook_client_secret,
            "authorize_scopes": "email"
        },
        AttributeMapping={
            'username': 'id',
            'email': 'email'
        }
    )

    logger.info(
        f"Response from creating user pool identity provider: "
        f"{json.dumps(response, default=lambda o: '<not serializable>')}"
    )


def __update(user_pool_id: str, facebook_client_id: str, facebook_client_secret: str):
    response = client.update_identity_provider(
        UserPoolId=user_pool_id,
        ProviderName='Facebook',
        ProviderDetails={
            'client_id': facebook_client_id,
            'client_secret': facebook_client_secret,
            "authorize_scopes": "email"
        },
        AttributeMapping={
            'username': 'id',
            'email': 'email'
        }
    )

    logger.info(
        f"Response from updating user pool identity provider: "
        f"{json.dumps(response, default=lambda o: '<not serializable>')}"
    )


def __delete(user_pool_id: str):
    try:
        response = client.delete_identity_provider(
            UserPoolId=user_pool_id,
            ProviderName='Facebook'
        )

        logger.info(
            f"Response from deleting user pool identity provider: "
            f"{json.dumps(response, default=lambda o: '<not serializable>')}"
        )
    except Exception as ex:
        logger.error(repr(ex))


def __handle(event, context):
    logger.info('Got new request. Event: {}, Context: {}'.format(event, context))

    user_pool_id = event['ResourceProperties']['UserPoolId']
    facebook_client_id = event['ResourceProperties']['FacebookClientId']
    facebook_client_secret = event['ResourceProperties']['FacebookClientSecret']

    if event['RequestType'] == 'Delete':
        __delete(user_pool_id)
        return

    if event['RequestType'] == 'Create':
        __create(user_pool_id, facebook_client_id, facebook_client_secret)
        return

    if event['RequestType'] == 'Update':
        __update(user_pool_id, facebook_client_id, facebook_client_secret)
        return

    raise KeyError('Unsupported request type! Type: {}'.format(event['RequestType']))


def handler(event, context):
    try:
        __handle(event, context)
    except Exception as ex:
        __failed(event, context, {'Error': str(ex)})
        return

    __success(event, context, {'Success': True})
