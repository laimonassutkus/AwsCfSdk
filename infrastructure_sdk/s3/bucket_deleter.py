from infrastructure_sdk.s3.abstract_s3_action import AbstractS3Action


class BucketDeleter(AbstractS3Action):
    def __init__(self):
        super().__init__()

    def delete_with_prefix(self, prefix: str):
        buckets = self.s3_client.list_buckets()

        for bucket in buckets['Buckets']:
            name = bucket['Name']  # type: str

            if name.startswith(prefix):
                s3_bucket = self.s3_resource.Bucket(name)
                s3_bucket.objects.all().delete()
                s3_bucket.delete()
