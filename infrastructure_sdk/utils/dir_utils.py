import os


class DirUtils:
    @staticmethod
    def exists(path: str):
        return os.path.exists(path)

    @staticmethod
    def create_if_not_exists(path: str):
        if not DirUtils.exists(path):
            os.makedirs(path)
