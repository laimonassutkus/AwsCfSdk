from troposphere.cloudformation import AWSCustomObject


class CustomCognitoFacebook(AWSCustomObject):
    resource_type = "Custom::CognitoFacebook"

    props = {
        'ServiceToken': (str, True),
        'UserPoolId': (str, True),
        'FacebookClientId': (str, True),
        'FacebookClientSecret': (str, True),
    }
