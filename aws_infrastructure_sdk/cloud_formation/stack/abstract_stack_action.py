import logging
import boto3

from typing import Optional
from abc import ABC


class AbstractStackAction(ABC):
    """
    Abstract class indicating an abstract cloud-formation stack action.
    More on cloud-formation:
    https://aws.amazon.com/cloudformation/
    """
    def __init__(self, cf_stack_name: str):
        """
        Constructor.

        :param cf_stack_name: The name of cloud-formation stack.
        """
        self.cf_stack_name = cf_stack_name
        self.cf_client = boto3.client('cloudformation')

    @staticmethod
    def get_logger(name: Optional[str] = None):
        """
        Creates logger instance.

        :param name: The name of the logger.

        :return: Logger instance.
        """
        return logging.getLogger(name or __name__)
