import logging
import subprocess

logr = logging.getLogger(__name__)


class ZappaDeployer:
    """
    Deploys zappa project.
    More on zappa tool:
    https://www.zappa.io/
    """
    def __init__(self, project_path: str, stage: str):
        """
        Constructor.

        :param project_path: Path to a zappa project.
        :param stage: Stage of the project (currently supported dev or prod).
        """
        assert stage in ['dev', 'prod'], 'Unsupported stage.'

        self.stage = stage
        self.project_path = project_path

    def deploy(self) -> bool:
        """
        Initiate zappa deployment.

        :return: A boolean value indicating whether deployment was successful.
        """
        deploy_command = (
            "cd {} "
            # We activate a virtual environment because zappa uses the active python
            # environment to package the dependencies.
            "&& . tmpenv/bin/activate "
            # We first call zappa update because it is most likely the 
            # project is deployed not the first time.
            "&& ( zappa update {} || zappa deploy {} )"
        ).format(self.project_path, self.stage, self.stage)

        try:
            logr.info('Deploying...')

            process = subprocess.Popen(
                deploy_command,
                shell=True,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            output, err = process.communicate()

            if process.returncode != 0:
                logr.info(output.decode())
                logr.error(err.decode())

            assert process.returncode == 0
            logr.info('Deployment successful.')
            return True
        except AssertionError as ex:
            logr.error(repr(ex))
            return False
