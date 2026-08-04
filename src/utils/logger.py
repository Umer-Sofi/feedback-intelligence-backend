"""Central logging setup so every module logs consistently."""

import logging

from src.core.config import get_settings

_configured = False


def get_logger(name: str) -> logging.Logger:
    """Return a named logger, configuring handlers once for the process."""
    global _configured
    if not _configured:
        settings = get_settings()
        logging.basicConfig(
            level=settings.log_level.upper(),
            format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        )
        _configured = True
    return logging.getLogger(name)
