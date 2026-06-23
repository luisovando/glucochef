"""
PHI audit log helper — Phase 5.

The `audit` async context manager writes one AuditLogEntry row per PHI
read or write operation. It is designed to be used as a FastAPI dependency
or called directly inside route handlers.

Usage (inside a route handler):
    from app.core.audit import audit
    from app.models.enums import AuditAction, AuditResource

    async with audit(
        session=db,
        actor=patient,
        action=AuditAction.write,
        resource=AuditResource.labs,
        resource_id=lab.id,
    ):
        lab = await lab_service.create(payload)

The audit entry is written unconditionally — even if the body raises an
exception — so that denied-access events are captured.

HIPAA note: the `resource` field stores only a resource-type identifier and
an optional UUID. Raw PHI values are never written to this table.
"""

import logging
import uuid
from contextlib import asynccontextmanager
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

from app.models.audit_log_entry import AuditLogEntry
from app.models.enums import AuditAction, AuditResource
from app.models.patient import Patient


@asynccontextmanager
async def audit(
    *,
    session: AsyncSession,
    actor: Patient,
    action: AuditAction,
    resource: AuditResource,
    resource_id: uuid.UUID | None = None,
    ip_address: str | None = None,
) -> AsyncIterator[None]:
    """
    Async context manager that writes one AuditLogEntry for a PHI operation.

    Args:
        session: The active SQLAlchemy async session.
        actor: The authenticated Patient performing the action.
        action: The audit action (AuditAction enum).
        resource: The resource type being accessed (AuditResource enum).
        resource_id: Optional UUID of the specific resource row.
        ip_address: Optional client IP address (never stored if None).

    Yields:
        None — the body of the ``async with`` block runs here.

    Raises:
        Any exception raised inside the block is re-raised after the entry
        is written, so callers always see the original error.
    """
    exc_to_reraise = None
    try:
        yield
    except Exception as exc:
        exc_to_reraise = exc
    finally:
        entry = AuditLogEntry(
            patient_id=actor.id,
            actor_cognito_sub=actor.cognito_sub,
            action=action,
            resource=resource,
            resource_id=resource_id,
            ip_address=ip_address,
        )
        session.add(entry)
        try:
            await session.flush()  # write within the current transaction
        except Exception as flush_exc:
            # If a body exception is already pending, log the flush failure
            # and let the original error propagate unchanged.
            if exc_to_reraise is not None:
                logger.error(
                    "audit flush failed (original error takes precedence): %s",
                    flush_exc,
                )
            else:
                raise

    if exc_to_reraise is not None:
        raise exc_to_reraise
