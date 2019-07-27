from setuptools import setup, find_packages
from infrastructure_sdk.setup_tools.setup_helper import prepare_setup, install_by_pip

# This is the very first thing that needs to be called.
prepare_setup()

PACKAGE_VERSION = '1.0.4'

INSTALL_REQUIRES = [
    'boto3'
]

setup(
    name='infrastructure_sdk',
    version=PACKAGE_VERSION,
    packages=find_packages(),
    include_package_data=True,
    description='SDK that helps to build infrastructure projects.',
)

[install_by_pip(dependency) for dependency in INSTALL_REQUIRES]
