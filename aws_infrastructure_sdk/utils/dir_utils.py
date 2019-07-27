import os


class DirUtils:
    """
    Utility class used for various actions with directories.
    """
    @staticmethod
    def exists(path: str) -> bool:
        """
        Tells whether the directory under given path exists.

        :param path: Path to a directory to check.

        :return: Boolean value indicating whether directory exists.
        """
        return os.path.exists(path)

    @staticmethod
    def create_if_not_exists(path: str) -> None:
        """
        Creates a directory if it does not exist.

        :param path: Path where a directory should be created.

        :return: No return.
        """
        if not DirUtils.exists(path):
            os.makedirs(path)
