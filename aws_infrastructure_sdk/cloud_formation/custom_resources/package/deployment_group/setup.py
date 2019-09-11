import os

from setuptools import setup

setup(
    name=os.path.basename(os.path.dirname(os.path.abspath(__file__))),
    version='1.0.0',
    install_requires=[
        'boto3==1.9.215',
        'botocore==1.12.215',
        'cfnresponse==1.0.1'
    ],
)
