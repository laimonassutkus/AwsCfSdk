from troposphere import AWSObject
from troposphere.validators import boolean


class CustomGitCommit(AWSObject):
    resource_type = "Custom::GitCommit"

    props = {
        'ServiceToken': (str, True),
        'RepositoryName': (str, True),
        'BranchName': (str, True),
        'ParentCommitId': (str, False),
        'AuthorName': (str, False),
        'Email': (str, False),
        'CommitMessage': (str, False),
        'KeepEmptyFolders': (bool, False),
        'PutFiles': ([dict], False),
        'DeleteFiles': ([dict], False),
        'SetFileModes': ([dict], False),
    }
