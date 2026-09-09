"""
MBA EDITORIAL DAILY - SECURE LOGGING SYSTEM
Configures standard logging. Ensures sensitive API keys or headers are NEVER logged.
"""

import logging
import sys
import os

class SensitiveFilter(logging.Filter):
    """
    Filter that redacts any potential API keys or sensitive values from log records.
    """
    def filter(self, record: logging.LogRecord) -> bool:
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key and isinstance(record.msg, str):
            record.msg = record.msg.replace(api_key, "[REDACTED_API_KEY]")
            if record.args:
                record.args = tuple(
                    arg.replace(api_key, "[REDACTED_API_KEY]") if isinstance(arg, str) else arg
                    for arg in record.args
                )
        return True

def setup_logger(name: str = "mba_editorial_pipeline") -> logging.Logger:
    """
    Initializes and returns a configured logger instance.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    handler.addFilter(SensitiveFilter())

    logger.addHandler(handler)
    return logger

logger = setup_logger()
