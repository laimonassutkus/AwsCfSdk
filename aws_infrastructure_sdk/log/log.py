from typing import Dict, Any


class Log:
    def __init__(self):
        pass

    @staticmethod
    def default_logging_formatters() -> Dict[str, Any]:
        return {
            'standard': {
                'format': '[%(levelname)-8s] '
                          'time: "%(asctime)s" '
                          'pid: "%(process)d" '
                          'tid: "%(thread)d" '
                          'module: "%(module)s" '
                          'message: "%(message)s"'
            },
            'console': {
                'format': '[%(levelname)-8s] '
                          'module: "%(module)s" '
                          'message: "%(message)s"'
            }
        }

    @staticmethod
    def default_logging_handlers() -> Dict[str, Any]:
        return {
            'null': {
                'level': 'DEBUG',
                'class': 'logging.NullHandler',
            },
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'console'
            },
        }

    @staticmethod
    def default_loggers() -> Dict[str, Any]:
        return {
            '': {
                'handlers': ['console'],
                'level': 'INFO',
                'propagate': True
            },
        }

    @staticmethod
    def default_logging_config() -> Dict[str, Any]:
        return {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': Log.default_logging_formatters(),
            'handlers': Log.default_logging_handlers(),
            'loggers': Log.default_loggers()
        }
