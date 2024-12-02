import sys
import traceback
import dotenv
import os
dotenv.load_dotenv()

LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")
LOG_FILE = os.getenv("LOG_FILE", "./logs/log.log")
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
from loguru import logger
from logtail import LogtailHandler
if os.getenv("LOGGER_TOKEN"):
    logtail_handler = LogtailHandler(source_token=os.getenv("LOGGER_TOKEN"))
else:
    logtail_handler = None

def format_error_message(exception:Exception):
    """format error message"""
    message = ""
    err_cls = exception.__class__.__name__
    detail = exception.args[0]
    _a, _b, _traceback = sys.exc_info()
    error_trace_back = []
    for _tb in traceback.extract_tb(_traceback):
        file_name = _tb[0]
        line_num = _tb[1]
        func_name = _tb[2]
        error_trace_back.append(f"{file_name}:{line_num}:{func_name}")
    error_msg = ",".join(error_trace_back)
    message += f"{err_cls}:{detail} TraceBack:[{error_msg}]"
    return message
# setup logger
logger.remove()
logger.add(
    sys.stdout,
    format="{time:YYYY-MM-D HH:mm:ss} | {level} | <level>{message}</level> {extra}",level=LOG_LEVEL,
)
if logtail_handler:
        logger.add(
            logtail_handler,
        level="DEBUG",
        backtrace=False,
        diagnose=False,
    )
logger.add(
    LOG_FILE,
    serialize=True,
    rotation="24 hours",
    retention="10 days",
)