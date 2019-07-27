from aws_infrastructure_sdk.s3.s3_abstract_action import AbstractS3Action


class S3BucketChecker(AbstractS3Action):
    """
    Checker class that does various checks against S3 buckets.
    """
    def is_empty(self, bucket_name: str):
        """
        Checks for contents in a given S3 bucket.

        :param bucket_name: The name of S3 bucket.

        :return: True if bucket empty, False otherwise.
        """
        resp = self.s3_client.list_objects_v2(Bucket=bucket_name)
        return len(resp['Contents']) == 0
