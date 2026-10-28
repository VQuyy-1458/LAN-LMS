import json
import time
from datetime import datetime, timezone
from ..models import AuditLogs, RealtimeEvents


def iso(value):
    return (
        datetime.fromtimestamp(value, timezone.utc).isoformat().replace("+00:00", "Z")
        if value is not None
        else None
    )


def audit(db, user_id, action, entity_type, entity_id, details=None):
    db.add(
        AuditLogs(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details_json=json.dumps(details or {}, ensure_ascii=False),
            created_at=time.time(),
        )
    )


def emit(db, event_type, course_id, data, owner_id=None):
    db.add(
        RealtimeEvents(
            event_type=event_type,
            course_id=course_id,
            owner_id=owner_id,
            data_json=json.dumps(data),
            created_at=time.time(),
        )
    )
