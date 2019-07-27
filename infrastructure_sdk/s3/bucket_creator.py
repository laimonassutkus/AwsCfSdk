from infrastructure_sdk.s3.abstract_s3_action import AbstractS3Action


class BucketCreator(AbstractS3Action):
    def __init__(self, bucket_name: str, region: str):
        super().__init__()

        self.region = region
        self.bucket_name = bucket_name

    def create(self):
        """
        Creates an S3 bucket if it does not exist.
        """
        exists = self.bucket_name in [bucket['Name'] for bucket in self.s3_client.list_buckets()['Buckets']]

        # If bucket does not exist - create it
        if not exists:
            self.get_logger().info('Bucket does not exist. Creating {}...'.format(self.bucket_name))

            self.s3_client.create_bucket(
                Bucket=self.bucket_name,
                ACL='private',
                CreateBucketConfiguration={
                    'LocationConstraint': self.region
                }
            )
        else:
            self.get_logger().info('Bucket {} already exists.'.format(self.bucket_name))
