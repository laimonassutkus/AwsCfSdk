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

        if self.__kwargs.get('autoRollbackConfiguration', {}).get('enabled') in ['true', 'True', True]:
            self.__kwargs['autoRollbackConfiguration']['enabled'] = True

        if self.__kwargs.get('autoRollbackConfiguration', {}).get('enabled') in ['false', 'False', False]:
            self.__kwargs['autoRollbackConfiguration']['enabled'] = False

        value = self.__kwargs.get('blueGreenDeploymentConfiguration', {}).get('terminateBlueInstancesOnDeploymentSuccess', {}).get('terminationWaitTimeInMinutes')
        if value:
            self.__kwargs['blueGreenDeploymentConfiguration']['terminateBlueInstancesOnDeploymentSuccess']['terminationWaitTimeInMinutes'] = int(value)

        return self

    @staticmethod
    def __inverse_capitalize(string: str) -> str:
        string = list(string)
        first = string[0].lower()
        string[0] = first
        return ''.join(string)
