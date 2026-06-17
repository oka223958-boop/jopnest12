"""
==============================================================
  utils/logger.py  —  Centralized Logger
==============================================================
  Call get_logger(__name__) in any module to get a logger
  that writes to BOTH the console AND a rotating log file.

  Usage:
      from utils.logger import get_logger
      log = get_logger(__name__)
      log.info("Model trained successfully")
      log.error("Something went wrong!")
==============================================================
"""

import logging
import os
from logging.handlers import RotatingFileHandler

# Import log directory from config
from config.settings import LOG_DIR


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Create (or retrieve) a named logger with console + file handlers.

    Args:
        name  : Usually pass __name__ so log lines show the module.
        level : Logging level (default INFO).

    Returns:
        A configured logging.Logger instance.
    """

    logger = logging.getLogger(name)

    # Avoid adding duplicate handlers if logger already configured
    if logger.handlers:
        return logger

    logger.setLevel(level)

    # ── Formatter: timestamp | level | module | message ──────────────
    fmt = logging.Formatter(
        fmt   = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt = "%Y-%m-%d %H:%M:%S",
    )
# ── Console Handler (prints to terminal) ─────────────────────────
# encoding='utf-8' fixes Windows terminal Unicode errors
    console_handler = logging.StreamHandler()
    console_handler.stream = open(1, "w", encoding="utf-8", closefd=False)
    console_handler.setFormatter(fmt)
    logger.addHandler(console_handler)
    # ── File Handler (rotates at 5 MB, keeps 3 backup files) ─────────
    log_path = os.path.join(LOG_DIR, "jobnest.log")
    file_handler = RotatingFileHandler(
        log_path, maxBytes=5 * 1024 * 1024, backupCount=3
    )
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    return logger
