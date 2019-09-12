import boto3

from typing import Any, Dict

client = boto3.client('codecommit')


class Commit:
    @staticmethod
    def create(**kwargs) -> Dict[str, Any]:
        kwargs = dict(
            repositoryName=kwargs.get('repositoryName'),
            branchName=kwargs.get('branchName'),
            parentCommitId=kwargs.get('parentCommitId'),
            authorName=kwargs.get('authorName'),
            email=kwargs.get('email'),
            commitMessage=kwargs.get('commitMessage'),
            keepEmptyFolders=kwargs.get('keepEmptyFolders'),
            putFiles=kwargs.get('putFiles'),
            deleteFiles=kwargs.get('deleteFiles'),
            setFileModes=kwargs.get('setFileModes'),
        )

        kwargs = {key: value for key, value in kwargs.items() if key and value}
        return client.create_commit(**kwargs)
