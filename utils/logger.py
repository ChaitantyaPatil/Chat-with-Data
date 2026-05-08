# ============================================================
#  Structured Logging Utility
#  Provides a consistent logger factory for all modules.
# ============================================================

from __future__ import annotations

import logging
import sys

from utils.config import get_settings


def get_logger(name: str) -> logging.Logger:
    """
    Create or retrieve a named logger with consistent formatting.

    Args:
        name: Logger name — typically ``__name__`` of the calling module.

    Returns:
        Configured :class:`logging.Logger` instance.
    """
    logger = logging.getLogger(name)

    # Avoid adding duplicate handlers on repeated calls
    if not logger.handlers:
        settings = get_settings()
        logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))

        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logger.level)

        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
