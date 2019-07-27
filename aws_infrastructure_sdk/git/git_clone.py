import logging
import subprocess

from aws_infrastructure_sdk.utils.dir_utils import DirUtils

logr = logging.getLogger(__name__)


class GitClone:
    """
    Wrapper class for git clone action.
    """
    def __init__(self, path_to_ssh_file: str):
        """
        Constructor.

        :param path_to_ssh_file: Path to an ssh file which allows to fetch protected repositories without password.
        More on git ssh files:
        https://git-scm.com/book/en/v2/Git-on-the-Server-Generating-Your-SSH-Public-Key
        """
        self.path_to_ssh_file = path_to_ssh_file

    def clone(self, git_url: str, download_path: str) -> None:
        """
        Clones a git repository.

        :param git_url: Repository url formatted for ssh use: e.g. git@bitbucket.org:person/repository.git
        :param download_path: Target path of where to clone.

        :return: No return.
        """
        DirUtils.create_if_not_exists(download_path)

        prcs = subprocess.Popen("bash", shell=True, stdin=subprocess.PIPE, stdout=None, stderr=subprocess.PIPE)
        stdout, stderr = prcs.communicate("ssh-agent $(ssh-add {}; git clone {} {})".format(
            self.path_to_ssh_file,
            git_url,
            download_path
        ).encode())

        if stdout:
            logr.info(stdout)

        if stderr:
            logr.error(stderr)
