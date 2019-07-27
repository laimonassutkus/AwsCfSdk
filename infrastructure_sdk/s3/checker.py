from s3.abstract_s3_action import AbstractS3Action


class S3Checker(AbstractS3Action):
    def is_empty(self, bucket_name: str):
        """
        Checks for contents in a given S3 bucket.

        :return: True if bucket empty, False otherwise.
        """
        resp = self.s3_client.list_objects_v2(Bucket=bucket_name)
        return len(resp['Contents']) == 0
