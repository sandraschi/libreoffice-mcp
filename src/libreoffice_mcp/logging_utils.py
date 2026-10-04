"""Ring buffer log handler for webapp Logs page."""

from __future__ import annotations

import logging
from collections import deque
from datetime import datetime
from typing import Any

log_buffer: deque[dict[str, Any]] = deque(maxlen=500)


class UIHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            log_buffer.append(
                {
                    "timestamp": datetime.fromtimestamp(record.created).isoformat(),
                    "level": record.levelname,
                    "name": record.name,
                    "message": self.format(record),
                    "exc_info": logging.Formatter().formatException(record.exc_info)
                    if record.exc_info
                    else None,
                }
            )
        except Exception:
            self.handleError(record)


def get_logs() -> list[dict[str, Any]]:
    return list(log_buffer)


def setup_ui_logging(level: int = logging.INFO) -> None:
    handler = UIHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    handler.setLevel(level)
    root = logging.getLogger()
    if not any(isinstance(h, UIHandler) for h in root.handlers):
        root.addHandler(handler)
