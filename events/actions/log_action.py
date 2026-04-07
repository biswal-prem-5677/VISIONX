"""
VisionX — Log Action
========================
Log events to file/database for audit and history.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from loguru import logger

from events.event_engine import EventAction
from shared.models import Event


class LogAction(EventAction):
    """Log events to file and/or console."""

    action_type = "log"

    def __init__(self, log_dir: str = "data/logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def execute(self, event: Event, context: dict[str, Any]) -> bool:
        """Log event to file."""
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "event_type": event.event_type,
                "source": event.source,
                "message": event.message,
                "severity": event.severity,
                "metadata": event.metadata,
            }

            # Log to daily file
            date_str = datetime.now().strftime("%Y-%m-%d")
            log_file = self.log_dir / f"events_{date_str}.jsonl"

            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, default=str) + "\n")

            logger.info(
                f"[LOG] {event.severity}: {event.message} "
                f"(source: {event.source})"
            )

            return True

        except Exception as e:
            logger.error(f"Log action error: {e}")
            return False
