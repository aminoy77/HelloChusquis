"""Structured JSON logging for HelloChusquis."""

import json
import logging
import os
import sys
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path


class JSONFormatter(logging.Formatter):
    """Outputs log records as JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "module": record.module,
            "message": record.getMessage(),
        }
        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry, ensure_ascii=False)


def get_logger(module_name: str) -> logging.Logger:
    """Return a configured logger for *module_name*.

    Writes JSON to ~/.hellochusquis/logs/hellochusquis.log (rotating, 5 MB, 3 backups).
    When DEBUG=1, also logs to stdout in the same JSON format.
    """
    logger = logging.getLogger(f"hellochusquis.{module_name}")

    # Avoid duplicate handlers on repeated calls
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # --- File handler (always) ---
    log_dir = Path.home() / ".hellochusquis" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(
        log_dir / "hellochusquis.log",
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(JSONFormatter())
    logger.addHandler(file_handler)

    # --- Console handler (DEBUG=1 only) ---
    if os.getenv("DEBUG") == "1":
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(JSONFormatter())
        logger.addHandler(console_handler)

    return logger
