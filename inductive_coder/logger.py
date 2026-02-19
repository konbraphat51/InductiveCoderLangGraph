"""Centralized logging setup for inductive coder.

Provides a single logger ("inductive_coder") that all workflow nodes write to.
Call setup_file_logging() from the CLI with output_dir to enable file logging.
"""

import logging
from pathlib import Path


LOGGER_NAME = "inductive_coder"
LOG_FILE_NAME = "run.log"

# Module-level logger used by all nodes
logger = logging.getLogger(LOGGER_NAME)
logger.setLevel(logging.DEBUG)

# Console handler (INFO level) added by default so logs also appear in stderr
_console_handler = logging.StreamHandler()
_console_handler.setLevel(logging.INFO)
_console_handler.setFormatter(
    logging.Formatter("[%(levelname)s] %(message)s")
)
logger.addHandler(_console_handler)


def setup_file_logging(output_dir: Path) -> logging.FileHandler:
    """Attach a real-time FileHandler that writes to output_dir/run.log.

    The handler flushes after every record so tail -f works immediately.
    Returns the handler so the caller can remove it if needed.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    log_path = output_dir / LOG_FILE_NAME

    file_handler = logging.FileHandler(log_path, mode="a", encoding="utf-8", delay=False)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    logger.addHandler(file_handler)

    logger.info("=== Run started. Log: %s ===", log_path)
    return file_handler


def teardown_file_logging(handler: logging.FileHandler) -> None:
    """Remove and close a file handler added by setup_file_logging."""
    logger.removeHandler(handler)
    handler.close()
