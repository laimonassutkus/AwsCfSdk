import logging
import boto3

from typing import Optional
from abc import ABC


class AbstractS3Action(ABC):
    """
    Abstract class which specifies a AWS S3 action.
    More on S3:
    https://aws.amazon.com/s3/
    """
    def __init__(self):
        """
        Constructor.
        """
        self.s3_client = boto3.client('s3')
        self.s3_resource = boto3.resource('s3')

    @staticmethod
    def get_logger(name: Optional[str] = None):
        """
        Returns a logger instance.

        :param name: Logger name

        :return: Logger instance.
        """
        return logging.getLogger(name or __name__)
