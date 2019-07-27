from aws_infrastructure_sdk.s3.s3_abstract_action import AbstractS3Action


class S3BucketDeleter(AbstractS3Action):
    """
    Class that deletes S3 buckets.
    """
    def __init__(self):
        """
        Constructor.
        """
        super().__init__()

    def delete_with_prefix(self, prefix: str) -> None:
        """
        Deletes buckets with specific prefixes.

        :param prefix: Prefix for bucket names.

        :return: No return.
        """
        buckets = self.s3_client.list_buckets()

        for bucket in buckets['Buckets']:
            name = bucket['Name']  # type: str

            if name.startswith(prefix):
                s3_bucket = self.s3_resource.Bucket(name)
                s3_bucket.objects.all().delete()
                s3_bucket.delete()
