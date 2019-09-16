import copy

from typing import Any, Dict


class Fixer:
    def __init__(self, kwargs: Dict[str, Any]):
        self.__kwargs = kwargs

    def get(self) -> Dict[str, Any]:
        return copy.deepcopy(self.__kwargs)

    def fix(self) -> 'Fixer':
        """
        Fixes lambda event resource parameters to comply with boto3 library parameters.

        :return: No return.
        """
        # All of the resource properties come with capitalized keys. Boto3 parameters start from lowercase.
        # Make sure to convert uppercase first char to a lowercase.
        self.__kwargs = {self.__inverse_capitalize(key): value for key, value in self.__kwargs.items()}

        # File contents must be bytes.
        if self.__kwargs.get('putFiles'):
            for put_file in self.__kwargs['putFiles']:
                if put_file.get('fileContent'):
                    file_content = put_file['fileContent']
                    if isinstance(file_content, str):
                        put_file['fileContent'] = file_content.encode()

        return self

    @staticmethod
    def __inverse_capitalize(string: str) -> str:
        string = list(string)
        first = string[0].lower()
        string[0] = first
        return ''.join(string)
