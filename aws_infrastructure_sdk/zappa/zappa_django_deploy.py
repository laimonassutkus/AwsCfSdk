import os
import shutil
import logging

from typing import Dict, Any
from aws_lambda.lambda_env_updater import LambdaEnvUpdater
from aws_infrastructure_sdk.cloud_formation.stack.api_gateway_describer import ApiGatewayDescriber
from aws_infrastructure_sdk.s3.s3_bucket_deleter import S3BucketDeleter
from aws_infrastructure_sdk.zappa.utils import run_bash, git_clone
from aws_infrastructure_sdk.zappa.zappa_env_updater import ZappaEnvUpdater
from aws_infrastructure_sdk.zappa.zappa_config import ZappaConfig

logr = logging.getLogger(__name__)


class ZappaDjangoDeploy:
    """
    Zappa - Django project deployment class.
    """
    DEFAULT_CLONE_PATH = '/tmp/zappa-django-tmp-project'

    def __init__(
            self,
            project_git_url: str,
            project_environment_vars: Dict[str, Any],
            zappa_environment_vars: Dict[str, Any],
            stage: str,
            deployed_project_name: str,
            ssh_file_path: str,
            aws_region: str
    ) -> None:
        """
        Constructor.

        :param project_git_url: Project under deployment git repository url.
        :param project_environment_vars: Project under deployment environment variables.
        :param zappa_environment_vars: Project's under deployment zappa environment variables.
        :param stage: Deployment stage (currently supported dev or prod).
        :param deployed_project_name: Name of the project in AWS infrastructure when it is deployed.
        :param ssh_file_path: Path to ssh file for git clone action without a password.
        :param aws_region: Region where the AWS infrastructure is.
        """
        assert stage in ['dev', 'prod'], 'Unsupported stage.'

        self.aws_region = aws_region
        self.ssh_file_path = ssh_file_path
        self.project_git_url = project_git_url
        self.project_environment = project_environment_vars
        self.zappa_environment = zappa_environment_vars
        self.stage = stage
        self.deployed_project_name = deployed_project_name
        self.deployed_project_name_with_stage = self.deployed_project_name + '-' + self.stage

        # We make sure in initial stage it allows all hosts.
        # Used so zappa deploy would not fail.
        self.project_environment['ALLOWED_HOST'] = '*'

    def deploy(self) -> None:
        """
        Initiates project deployment.

        :return: No return.
        """
        logr.info(
            f'Initiating project deployment. Context:'
            f'\nRegion: {self.aws_region},'
            f'\nSSH file path: {self.ssh_file_path},'
            f'\nProject git url: {self.project_git_url},'
            f'\nProject environment: {self.project_environment},'
            f'\nZappa environment: {self.zappa_environment},'
            f'\nStage: {self.stage},'
            f'\nDeployed project name: {self.deployed_project_name},'
            f'\nDeployed project name with stage: {self.deployed_project_name_with_stage}.'
        )

        # Clean previous failed builds.
        self.__clean()

        logr.info(f'Downloading {self.deployed_project_name_with_stage} project...')
        git_clone(self.project_git_url, self.DEFAULT_CLONE_PATH, self.ssh_file_path)

        logr.info(f'Updating {self.deployed_project_name_with_stage} zappa settings...')
        ZappaEnvUpdater(self.DEFAULT_CLONE_PATH).update(self.project_environment, self.zappa_environment)

        # Install all dependencies.
        self.__install()
        # Run tests and assert whether it can be deployed to servers.
        self.__test()
        # Deploy to servers.
        self.__deploy()
        # Clean build dirs.
        self.__clean()

        # Zappa deploys lambda function and creates an api gateway.
        # The gateway host must be added to django security hosts.
        api_gateway_id = ApiGatewayDescriber(self.deployed_project_name_with_stage).describe()

        logr.info('Updating lambda environment...')
        self.project_environment['ALLOWED_HOST'] = '{}.execute-api.{}.amazonaws.com'.format(api_gateway_id, self.aws_region)
        LambdaEnvUpdater(self.deployed_project_name_with_stage).update(self.project_environment)

        logr.info('Deployment fully configured and successful!')

    def __clean(self):
        """
        Deletes build leftovers.

        :return: No return.
        """
        # Delete build leftovers
        logr.info(f'Deleting build leftovers for {self.deployed_project_name_with_stage}...')
        try:
            shutil.rmtree(self.DEFAULT_CLONE_PATH)
        except FileNotFoundError:
            pass

        # Delete upload leftovers
        logr.info(f'Deleting zappa buckets for {self.deployed_project_name_with_stage}...')
        # When deploying with zappa a lot of buckets are being created. Delete them.
        S3BucketDeleter().delete_with_prefix('zappa')

    def __test(self):
        """
        Runs projects tests.

        :return: No return.
        """
        # Create dotenv file for testing .
        self.__create_dot_env()

        test_command = (
            "cd {} "
            # Source the virtual env.
            "&& . tmpenv/bin/activate "
            # Run django tests.
            "&& echo "
            "&& python manage.py test --noinput".format(self.DEFAULT_CLONE_PATH)
        )

        logr.info(f'Running tests for {self.deployed_project_name_with_stage}...')
        success = run_bash(test_command)
        assert success, 'Tests failed!'
        logr.info(f'Tests succeeded for {self.deployed_project_name_with_stage}!')

        # After testing delete the file.
        self.__delete_dot_env()

    def __create_dot_env(self):
        """
        Creates dot-env file for storing environment.

        :return: No return.
        """
        with open(self.DEFAULT_CLONE_PATH + '/.env', 'w') as env:
            for key, value in self.project_environment.items():
                env.write(key + '=' + value + '\n')

    def __delete_dot_env(self):
        """
        Deletes dot-env file.

        :return: No return.
        """
        os.remove(self.DEFAULT_CLONE_PATH + '/.env')

    def __install(self):
        """
        Installs projects with it's dependencies.

        :return: No return.
        """
        install_command = (
            "cd {} "
            "&& virtualenv tmpenv --python=python3"
            "&& . tmpenv/bin/activate"
            # Every nj project must contain install.sh script at the root directory
            # which will fully install an configure the system to successfully run the project.
            "&& ./install.sh python {}"
            # Install zappa to enable deployment.
            "&& pip install zappa=={}".format(
                self.DEFAULT_CLONE_PATH,
                self.stage,
                ZappaConfig.VERSION
            ))

        logr.info(f'Installing {self.deployed_project_name_with_stage} project...')
        success = run_bash(install_command)
        assert success, 'Installation failed!'
        logr.info('Installation succeeded!')

    def __deploy(self):
        """
        Deploys project.

        :return: None.
        """
        deploy_command = (
            "cd {} "
            # We activate a virtual environment because zappa uses the active python
            # environment to package the dependencies.
            "&& . tmpenv/bin/activate "
            "&& ( zappa update {} || zappa deploy {} )"
        ).format(self.DEFAULT_CLONE_PATH, self.stage, self.stage)

        logr.info(f'Deploying {self.deployed_project_name_with_stage}...')
        success = run_bash(deploy_command)
        assert success, 'Deployment failed.'
        logr.info(f'Deployment for {self.deployed_project_name_with_stage} was successfull!')
