import os
import sys
from loguru import logger

LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")
LOG_FILE = os.getenv("LOG_FILE", "./logs/log.log")
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

def setup_logger():
    # setup logger
    from loguru import logger
    logger.remove()
    workflow_logger = logger.bind(name="workflow")
    workflow_logger.add(
        sys.stdout,
        format="{time:YYYY-MM-D HH:mm:ss} | {level} | <level>{message}</level> {extra}",
        level=LOG_LEVEL,
    )
    workflow_logger.add(LOG_FILE, serialize=True, rotation="24 hours", retention="10 days")

setup_logger()