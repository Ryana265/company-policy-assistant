"""Loguru setup.

Our code logs with `from loguru import logger`. Libraries like uvicorn and
FastAPI use Python's built-in `logging`, so InterceptHandler forwards those
records to loguru too. Everything comes out in one format.
"""
import inspect
import logging
import sys

from loguru import logger


class InterceptHandler(logging.Handler):
    """Send standard `logging` records to loguru (recipe from the loguru docs)."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level: str | int = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find the code that made the logging call, so loguru reports the right file and line.
        frame, depth = inspect.currentframe(), 0
        while frame and (depth == 0 or frame.f_code.co_filename == logging.__file__):
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def setup_logging(level: str) -> None:
    logger.remove()  # drop loguru's default handler so lines aren't printed twice
    logger.add(
        sys.stderr,
        level=level.upper(),
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
        ),
        backtrace=False,  # keep tracebacks short; set True when debugging
        diagnose=False,   # never print variable values (they can contain API keys)
    )

    # Route all standard logging (uvicorn, fastapi, ...) through loguru.
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"):
        std_logger = logging.getLogger(name)
        std_logger.handlers = [InterceptHandler()]
        std_logger.propagate = False

    # The HTTP libraries log every request at INFO; keep them quiet.
    for noisy in ("httpx", "httpx2", "httpcore"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
