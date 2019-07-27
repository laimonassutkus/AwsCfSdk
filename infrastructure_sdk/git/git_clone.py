import logging
import subprocess

from infrastructure_sdk.utils.dir_utils import DirUtils

logr = logging.getLogger(__name__)


class GitClone:
    def __init__(self, path_to_ssh_file: str):
        self.path_to_ssh_file = path_to_ssh_file

    def clone(self, git_url: str, download_path: str):
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
