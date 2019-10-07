import logging
import subprocess

logr = logging.getLogger(__name__)


def run_bash(command: str) -> bool:
    """
    Execute the command in bash shell.

    :return: Boolean value indicating whether command executed successfully.
    """
    process = subprocess.Popen(
        command,
        shell=True,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    output, err = process.communicate()

    if process.returncode != 0:
        logr.info(output.decode())
        logr.error(err.decode())

    return process.returncode == 0


def git_clone(git_url: str, download_path: str, path_to_git_ssh_file: str) -> None:
    """
    Clones a git repository.

    :param git_url: Repository url formatted for ssh use: e.g. git@bitbucket.org:person/repository.git
    :param download_path: Target path of where to clone.

    :return: No return.
    """
    prcs = subprocess.Popen("bash", shell=True, stdin=subprocess.PIPE, stdout=None, stderr=subprocess.PIPE)
    stdout, stderr = prcs.communicate("ssh-agent $(ssh-add {}; git clone {} {})".format(
        path_to_git_ssh_file,
        git_url,
        download_path
    ).encode())

    if stdout:
        logr.info(stdout)

    if stderr:
        logr.error(stderr)
