import logging
import subprocess

logr = logging.getLogger(__name__)


class BashCommand:
    """
    Wrapper class for bash command execution.
    """
    def __init__(self, command: str):
        """
        Constructor.

        :param command: Command to execute in bash shell.
        """
        self.command = command

    def run(self) -> bool:
        """
        Execute the command.

        :return: Boolean value indicating whether command executed successfully.
        """
        process = subprocess.Popen(
            self.command,
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
