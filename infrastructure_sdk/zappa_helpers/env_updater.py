import json
import logging
import os

from typing import Any, Dict

logr = logging.getLogger(__name__)


class EnvUpdater:
    READ_AND_OVERRIDE = 'r+'

    def __init__(self, project_path: str):
        self.project_path = project_path

    def update(self, project_environment: Dict[str, Any], zappa_environment: Dict[str, Any]):
        """
        Updates zappa_settings.json file for a django zappa project.

        :param project_environment: Environment variables for the django project.
        :param zappa_environment:  Environment variables for zappa.
        """
        logr.info('Updating zappa settings...')

        with open(os.path.join(self.project_path, 'zappa_settings.json'), self.READ_AND_OVERRIDE) as settings:
            settings_dict = json.loads(settings.read())

            # Cycle through every stage (dev, prod, etc.)
            for settings_stage_key, stage_dict in settings_dict.items():
                stage_environment = settings_dict[settings_stage_key]

                # Update project env variables
                stage_environment['environment_variables'] = project_environment

                # Update zappa settings
                for key, value in zappa_environment.items():
                    stage_environment[key] = value


            settings_string = json.dumps(settings_dict)
            settings.seek(0)
            settings.write(settings_string)
