"""
Phase 5 — AC2: PHI route call produces exactly one audit_log_entries row.

TDD RED: these tests FAIL until app/core/audit.py is implemented.
"""

import uuid
from datetime import date
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select

from app.models.audit_log_entry import AuditLogEntry
from app.models.patient import Patient
from app.models.enums import AuditAction, AuditResource


@pytest.fixture
async def patient_row(db_session):
    """Insert a minimal Patient row and return it."""
    p = Patient(
        cognito_sub=f"test-sub-{uuid.uuid4()}",
        consent_accepted=True,
        consent_accepted_on=date.today(),
    )
    db_session.add(p)
    await db_session.commit()
    await db_session.refresh(p)
    return p


async def test_audit_context_manager_writes_one_row(db_session, patient_row):
    """
    AC2 — Using the audit context manager produces exactly one AuditLogEntry row
    with the correct actor_id and action.

    This test FAILS until app/core/audit.py exists and is implemented.
    """
    from app.core.audit import audit

    resource_id = uuid.uuid4()

    async with audit(
        session=db_session,
        actor=patient_row,
        action=AuditAction.write,
        resource=AuditResource.labs,
        resource_id=resource_id,
    ):
        pass  # simulates the body of a PHI route

    result = await db_session.execute(
        select(AuditLogEntry).where(AuditLogEntry.patient_id == patient_row.id)
    )
    entries = result.scalars().all()

    assert len(entries) == 1, f"Expected 1 audit entry, got {len(entries)}"
    entry = entries[0]
    assert entry.actor_cognito_sub == patient_row.cognito_sub
    assert entry.action == AuditAction.write
    assert entry.resource == AuditResource.labs
    assert entry.resource_id == resource_id


async def test_audit_context_manager_still_writes_row_on_exception(db_session, patient_row):
    """
    The audit entry must be written even when the body of the context manager raises.
    This ensures denied-access events are also recorded.
    """
    from app.core.audit import audit

    with pytest.raises(ValueError, match="simulated error"):
        async with audit(
            session=db_session,
            actor=patient_row,
            action=AuditAction.read,
            resource=AuditResource.labs,
        ):
            raise ValueError("simulated error")

    result = await db_session.execute(
        select(AuditLogEntry).where(AuditLogEntry.patient_id == patient_row.id)
    )
    entries = result.scalars().all()
    assert len(entries) == 1, "Audit entry must be written even when an exception occurs"


async def test_original_exception_not_masked_when_flush_fails(db_session, patient_row):
    """
    When the body raises AND session.flush() also raises, the original body
    exception must propagate — the flush error must not replace it.
    """
    from app.core.audit import audit

    with patch.object(
        db_session, "flush", new_callable=AsyncMock, side_effect=RuntimeError("flush failed")
    ):
        with pytest.raises(ValueError, match="original error"):
            async with audit(
                session=db_session,
                actor=patient_row,
                action=AuditAction.write,
                resource=AuditResource.labs,
            ):
                raise ValueError("original error")
