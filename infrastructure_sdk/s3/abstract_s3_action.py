import logging
import boto3

from typing import Optional
from abc import ABC


class AbstractS3Action(ABC):
    def __init__(self):
        self.s3_client = boto3.client('s3')
        self.s3_resource = boto3.resource('s3')

    def get_logger(self, name: Optional[str] = None):
        return logging.getLogger(name or __name__)
