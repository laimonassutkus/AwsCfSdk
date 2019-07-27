import logging
import subprocess

logr = logging.getLogger(__name__)


class BashCommand:
    def __init__(self, command: str):
        self.command = command

    def run(self) -> bool:
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
