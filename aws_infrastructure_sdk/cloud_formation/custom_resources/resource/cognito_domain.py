from troposphere.cloudformation import AWSCustomObject


class CustomCognitoDomain(AWSCustomObject):
    resource_type = "Custom::CognitoDomain"

    props = {
        'ServiceToken': (str, True),
        'UserPoolId': (str, True),
        'DomainName': (str, True),
    }
