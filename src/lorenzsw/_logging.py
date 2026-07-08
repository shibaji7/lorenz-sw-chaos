"""Shared Loguru helpers."""

from __future__ import annotations

import sys

from loguru import logger


def configure_logging(level: str = "INFO") -> None:
    """Configure a compact stderr logger for scripts and CLI entry points."""

    logger.remove()
    logger.add(
        sys.stderr,
        level=level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level:<8} | {message}",
    )
