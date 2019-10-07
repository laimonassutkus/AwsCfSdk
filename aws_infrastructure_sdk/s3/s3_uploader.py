import datetime
import ntpath

from io import BytesIO
from aws_infrastructure_sdk.s3.s3_abstract_action import AbstractS3Action


class S3Uploader(AbstractS3Action):
    def __init__(self, bucket_name: str):
        super().__init__()
        self.bucket_name = bucket_name

    def upload_bytes(self, bytes_object: bytes):
        """
        Uploads bytes object to a specified bucket and returns a pre-signed url.
        """
        self.get_logger().info('Uploading bytes object to S3...')

        bucket = self.s3_resource.Bucket(self.bucket_name)

        output = BytesIO()
        output.write(bytes_object)
        output.seek(0)

        s3_obj_name = str(datetime.datetime.now())
        bucket.upload_fileobj(output, s3_obj_name)

        s3_url = self.s3_client.generate_presigned_url('get_object', Params={
            'Bucket': self.bucket_name,
            'Key': s3_obj_name
        })

        self.get_logger().info('Finished uploading bytes object to S3.')

        return s3_url

    def upload_file(self, path_to_file: str):
        """
        Uploads a file in a given bucket and returns a pre-signed url.
        """
        self.s3_client.upload_file(path_to_file, self.bucket_name, ntpath.basename(path_to_file))

        return self.s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': self.bucket_name, 'Key': ntpath.basename(path_to_file)}
        )
