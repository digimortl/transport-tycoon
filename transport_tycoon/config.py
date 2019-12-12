LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            'format': '%(levelname)s: %(message)s'
        },
    },
    'handlers': {
        'null': {
            'class': 'logging.NullHandler',
        },
        'console': {
            'level': 'DEBUG',
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stderr',
        },
    },
    'loggers': {
        'transport_tycoon': {
            'handlers': ['null'],
            'level': 'DEBUG',
            'propagate': False,
        },
        '__main__': {
            'handlers': ['null'],
            'level': 'DEBUG',
            'propagate': False
        },
    }
}