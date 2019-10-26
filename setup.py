from setuptools import setup, find_packages

setup(
    name='aws_infrastructure_sdk',
    version='2.1.0',
    license='GNU GENERAL PUBLIC LICENSE Version 3',
    packages=find_packages(),
    description='SDK that helps to build AWS - CloudFormation infrastructure projects.',
    include_package_data=True,
    install_requires=[
        'boto3',
        'botocore',
        'troposphere',
        'cfnresponse',
        'aws-cf-custom-resources',
        'aws-lambda'
    ],
    author='Laimonas Sutkus',
    author_email='laimonas.sutkus@gmail.com',
    keywords='AWS SDK CloudFormation Zappa Infrastructure Cloud',
    url='https://github.com/laimonassutkus/AwsInfrastructureSdk',
    classifiers=[
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Operating System :: OS Independent',
    ],
)
