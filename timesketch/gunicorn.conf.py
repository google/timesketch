import json
import logging
import time
import os


class JSONFormatter(logging.Formatter):
    def format(self, record):
        level = record.levelname.upper()
        severity = "WARNING" if level == "WARN" else level
        log_record = {
            "message": record.getMessage(),
            "severity": severity,
            "timestamp": time.strftime(
                "%Y-%m-%dT%H:%M:%SZ", time.gmtime(record.created)
            ),
            "logger": record.name,
        }
        return json.dumps(log_record)


USE_STRUCTURED_LOGGING = (
    os.environ.get("ENABLE_STRUCTURED_LOGGING", "false").lower() == "true"
)

STRUCTURED_LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": JSONFormatter,
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "formatter": "json",
        }
    },
    "loggers": {
        "gunicorn.error": {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": False,
        },
        "gunicorn.access": {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": False,
        },
    },
}

if USE_STRUCTURED_LOGGING:
    logconfig_dict = STRUCTURED_LOGGING_CONFIG
else:
    pass
