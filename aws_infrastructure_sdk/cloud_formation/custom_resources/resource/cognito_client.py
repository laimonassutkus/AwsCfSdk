from troposphere import AWSObject
from troposphere.validators import boolean, positive_integer


class CustomUserPoolClient(AWSObject):
    resource_type = "AWS::Cognito::UserPoolClient"

    props = {
        'ClientName': (str, False),
        'ExplicitAuthFlows': ([str], False),
        'GenerateSecret': (boolean, False),
        'ReadAttributes': ([str], False),
        'RefreshTokenValidity': (positive_integer, False),
        'UserPoolId': (str, True),
        'WriteAttributes': ([str], False),
        'CallbackURLs': ([str], False),
        'DefaultRedirectURI': (str, False),
        'LogoutURLs': ([str], False),
        'SupportedIdentityProviders': ([str], False),
        'AllowedOAuthScopes': ([str], False),
        'AllowedOAuthFlows': ([str], False),
        'AllowedOAuthFlowsUserPoolClient': (bool, False),
    }
