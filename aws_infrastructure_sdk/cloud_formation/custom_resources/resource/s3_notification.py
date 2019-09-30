from troposphere import AWSObject


class CustomS3Notification(AWSObject):
    resource_type = "Custom::S3Notification"

    props = {
        'ServiceToken': (str, True),
        'BucketName': (str, True),
        'NotificationConfiguration': (dict, True),
    }
