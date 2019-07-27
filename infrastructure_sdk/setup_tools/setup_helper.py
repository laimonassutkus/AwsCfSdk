import subprocess
import sys

from setuptools.command.install import install
from infrastructure_sdk.git.version_resolver import GitVersionResolver

ENVIRONMENT = None


class InstallCommand(install):
    user_options = install.user_options + [
        ('environment=', None, 'Specify a production or development environment.'),
    ]

    def initialize_options(self):
        install.initialize_options(self)
        self.environment = None

    def finalize_options(self):
        install.finalize_options(self)

        global ENVIRONMENT

        try:
            # Check if environment is set
            is_dev()
        except AssertionError:
            # If not - assert that this class has a set environment
            assert self.environment in ['dev', 'prod'], 'Bad environment propagated from parent project.'
            ENVIRONMENT = self.environment

    def run(self):
        install.run(self)


def install_from_git(name, version, git_repo_name):
    """
    Installs a python package from a git repository.
    """
    if not is_installing():
        return

    # Resolve supplied version with git tags
    dependency_version = GitVersionResolver(git_repo_name).resolve(version, is_dev())
    # Make sure version was resolved
    assert dependency_version, 'Bad version supplied for {}. Version: {}'.format(name, version)
    print("Resolved version for {}: {}".format(version, dependency_version))
    # Create a dependency link
    dep_link = 'git+ssh://git@bitbucket.org/{}.git@{}'.format(git_repo_name, ("dev-" if is_dev() else '') + dependency_version)

    # Install dependency through pip
    command = [sys.executable, "-m", "pip", "install", dep_link]
    command.extend(['--install-option=--environment={}'.format('dev' if is_dev() else 'prod')])
    subprocess.check_call(command)


def install_by_pip(dependency):
    if not is_installing():
        return

    # Install dependency through pip
    command = [sys.executable, "-m", "pip", "install", dependency]
    subprocess.check_call(command)


def is_installing():
    return "install" in sys.argv


def is_dev():
    """
    Determines whether setup is running in development or production environment
    """
    dev = "dev" == ENVIRONMENT
    prod = "prod" == ENVIRONMENT

    assert (prod or dev) is True, 'Environment should be set to dev or prod'
    assert (prod and dev) is False, 'Environment can not be both prod and dev at the same time'

    return dev


def prepare_setup():
    """
    Ensures that setup() can be called without errors and environment is set.
    """
    global ENVIRONMENT

    if not is_installing():
        return

    if "dev" in sys.argv:
        sys.argv.remove("dev")
        ENVIRONMENT = "dev"

    if "prod" in sys.argv:
        sys.argv.remove("prod")
        ENVIRONMENT = "prod"
