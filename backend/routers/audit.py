"""
Audit log endpoint.

WHY: auditability is a core goal, so the trail of who did what must be
readable, not only written. Read-only: audit rows are never edited or deleted.
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import get_db
from models import AuditLog
from schemas import AuditLogResponse

router = APIRouter(tags=["Audit"])


@router.get("/audit-log", response_model=list[AuditLogResponse])
def list_audit_log(
    entity_id: Optional[str] = None,
    entity_type: Optional[str] = None,
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Audit rows, newest first. Every filter is optional."""
    query = db.query(AuditLog)
    if entity_id:
        query = query.filter(AuditLog.entity_id == entity_id)
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if action:
        query = query.filter(AuditLog.action == action)
    return query.order_by(AuditLog.timestamp.desc()).limit(limit).all()