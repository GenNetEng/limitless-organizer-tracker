"""Centralized event logging service (FR19).

All significant application operations should call log_event() to record
an entry in the event_log table. This function is exception-safe — it
never raises, so it can be called from any context without risk to the caller.
"""

import json
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db.models import EventLog

logger = logging.getLogger(__name__)


def log_event(
    *,
    session: Session | None,
    event_type: str,
    source: str,
    message: str,
    severity: str = "INFO",
    details: dict | None = None,
    correlation_id: str | None = None,
) -> None:
    try:
        if session is None:
            return
        row = EventLog(
            timestamp=datetime.now(timezone.utc),
            event_type=event_type,
            severity=severity,
            source=source,
            message=message,
            details=json.dumps(details) if details is not None else None,
            correlation_id=correlation_id,
        )
        session.add(row)
        session.flush()
    except Exception:
        logger.debug("Failed to write event log entry", exc_info=True)
