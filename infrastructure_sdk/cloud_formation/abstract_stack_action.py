import logging
import boto3

from typing import Optional
from abc import ABC


class AbstractStackAction(ABC):
    def __init__(self, cf_stack_name: str):
        self.cf_stack_name = cf_stack_name
        self.cf_client = boto3.client('cloudformation')

    def get_logger(self, name: Optional[str] = None):
        return logging.getLogger(name or __name__)
