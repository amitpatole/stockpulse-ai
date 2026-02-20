"""
Structured JSONL event emitter for infra incidents (VO-036).

Events are written to logs/infra-incidents.jsonl and mirrored to the
standard Python logger so they appear in logs/backend.log as well.
"""

import json
import logging
import os
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

_DEFAULT_JSONL_PATH = "logs/infra-incidents.jsonl"


class IncidentLog:
    """Append structured events to a JSONL file and to the Python log."""

    def __init__(self, jsonl_path: str = _DEFAULT_JSONL_PATH) -> None:
        self._path = jsonl_path

    def emit(self, event: dict) -> None:
        """Append *event* to the JSONL log, adding an ISO-8601 timestamp."""
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **event,
        }
        logger.info("infra-incident: %s", record)
        log_dir = os.path.dirname(self._path)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        with open(self._path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record) + "\n")
