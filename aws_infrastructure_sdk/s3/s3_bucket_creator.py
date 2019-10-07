import time

from botocore.exceptions import ClientError
from aws_infrastructure_sdk.s3.s3_abstract_action import AbstractS3Action


class S3BucketCreator(AbstractS3Action):
    def __init__(self, bucket_name: str, region: str):
        """
        Constructor.

        :param bucket_name: The name of S3 bucket.
        :param region: Region where a bucket exists.
        """
        super().__init__()

        self.region = region
        self.bucket_name = bucket_name

    def create(self, recursion: bool = False) -> None:
        """
        Creates an S3 bucket if it does not exist.

        :param recursion: Indicates if this function is in recursion.

        :return: No return.
        """
        exists = self.bucket_name in [bucket['Name'] for bucket in self.s3_client.list_buckets()['Buckets']]

        # If bucket does not exist - create it.
        if not exists:
            self.get_logger().info('Bucket does not exist. Creating {}...'.format(self.bucket_name))

            try:
                self.s3_client.create_bucket(
                    Bucket=self.bucket_name,
                    ACL='private',
                    CreateBucketConfiguration={
                        'LocationConstraint': self.region
                    }
                )
            except ClientError as ex:
                if recursion is True:
                    raise

                if ex.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
                    self.get_logger().info('Bucket {} already exists.'.format(self.bucket_name))
                elif ex.response['Error']['Code'] == 'OperationAborted':
                    time.sleep(2)
                    self.create(True)
                else:
                    raise
        else:
            self.get_logger().info('Bucket {} already exists.'.format(self.bucket_name))
