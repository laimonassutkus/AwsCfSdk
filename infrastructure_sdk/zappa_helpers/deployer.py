import logging

from infrastructure_sdk.bash.command import BashCommand

logr = logging.getLogger(__name__)


class Deployer:
    def __init__(self, project_path: str, stage: str):
        assert stage in ['dev', 'prod'], 'Unsupported stage.'

        self.stage = stage
        self.project_path = project_path

    def deploy(self):
        deploy_command = (
            "cd {} "
            # We activate a virtual environment because zappa uses the active python
            # environment to package the dependencies.
            "&& . tmpenv/bin/activate "
            "&& ( zappa update {} || zappa deploy {} )"
        ).format(self.project_path, self.stage, self.stage)

        try:
            logr.info('Deploying...')
            success = BashCommand(deploy_command).run()
            assert success, 'Deployment failed.'
            logr.info('Deployment successful.')
            return True
        except AssertionError as ex:
            logr.error(repr(ex))
            return False
