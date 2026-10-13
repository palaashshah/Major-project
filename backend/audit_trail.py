"""
One place for writing audit rows.

WHY: every mutating action must leave a record of who did what and when.
The caller commits, so the audit row is saved together with the change.
"""
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from models import AuditLog


def plain(value):
    """Make a stored value safe to put in a JSON column."""
    return float(value) if isinstance(value, Decimal) else value


def record_audit(db: Session, user_id: Optional[str], action: str, entity_type: str,
                 entity_id: str, reason: Optional[str] = None,
                 before: Optional[dict] = None, after: Optional[dict] = None) -> None:
    db.add(AuditLog(
        id=str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc),
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        reason=reason,
        before=before,
        after=after,
    ))