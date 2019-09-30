import json
import logging
import boto3

from typing import Any, Dict

client = boto3.client('s3')
logger = logging.getLogger()
logger.setLevel(logging.INFO)


class Notification:
    @staticmethod
    def create(**kwargs) -> Dict[str, Any]:
        kwargs = dict(
            Bucket=kwargs.get('bucketName'),
            NotificationConfiguration=kwargs.get('notificationConfiguration')
        )

        kwargs = {key: value for key, value in kwargs.items() if key and value}

        logger.info(
            f'Calling aws with given arguments: '
            f'{json.dumps(kwargs, default=lambda o: "<not serializable>")}.'
        )

        return client.put_bucket_notification_configuration(**kwargs)
