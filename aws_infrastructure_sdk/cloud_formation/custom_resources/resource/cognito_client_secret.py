from troposphere.cloudformation import AWSCustomObject


class CustomCognitoClientSecret(AWSCustomObject):
    resource_type = "Custom::CognitoClientSecret"

    props = {
        'ServiceToken': (str, True),
        'UserPoolId': (str, True),
        'ClientId': (str, True),
    }
