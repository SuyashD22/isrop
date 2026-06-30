"""
src/utils/logger.py
Structured logging with timestamps and log levels.
Configures both file and console handlers.
"""

from __future__ import annotations

import logging
import sys
from datetime import datetime
from pathlib import Path


def setup_logger(
    name: str = "lissclear",
    level: int = logging.INFO,
    log_dir: Path = None,
    console: bool = True,
) -> logging.Logger:
    """
    Set up a structured logger with optional file output.

    Args:
        name:    Logger name (use module __name__ for module-level loggers).
        level:   Logging level (logging.DEBUG, INFO, WARNING, etc.).
        log_dir: If set, writes log file to log_dir/lissclear_YYYYMMDD.log.
        console: Whether to output to stdout.

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding duplicate handlers
    if logger.handlers:
        return logger

    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    if console:
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(level)
        ch.setFormatter(fmt)
        logger.addHandler(ch)

    if log_dir:
        log_dir = Path(log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        fh = logging.FileHandler(log_dir / f"lissclear_{date_str}.log")
        fh.setLevel(level)
        fh.setFormatter(fmt)
        logger.addHandler(fh)

    return logger


# Module-level root logger
root_logger = setup_logger("lissclear")
