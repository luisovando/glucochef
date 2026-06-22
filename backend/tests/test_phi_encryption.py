"""
Phase 5 — AC1: PHI encryption at rest.

TDD RED: these tests FAIL until EncryptedString in app/core/crypto.py
is replaced by the real Fernet TypeDecorator.
"""

import uuid
from datetime import date

import pytest
from sqlalchemy import text

from app.models.lab_result import LabResult
from app.models.patient import Patient
from app.models.enums import LabKind, LabUnit


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


async def test_lab_value_is_stored_as_ciphertext(db_session, patient_row):
    """
    AC1 — Writes a LabResult via ORM, then reads the raw column value directly
    (bypassing the ORM type system) and asserts it is NOT the original plaintext.

    This test FAILS while EncryptedString = Text (Phase 3 placeholder).
    It passes once the real Fernet TypeDecorator is in place (Phase 5).
    """
    plaintext = "7.2"
    lab = LabResult(
        patient_id=patient_row.id,
        kind=LabKind.hba1c,
        value=plaintext,
        unit=LabUnit.percent,
        sample_date=date.today(),
    )
    db_session.add(lab)
    await db_session.commit()

    # Bypass the ORM and read the raw bytes stored in the column.
    raw_result = await db_session.execute(
        text("SELECT value FROM lab_results LIMIT 1")
    )
    raw_value = raw_result.scalar()

    assert raw_value != plaintext, (
        f"PHI column 'value' must store ciphertext, but found plaintext: {raw_value!r}"
    )


async def test_lab_value_round_trips_through_orm(db_session, patient_row):
    """
    Companion test: ORM must decrypt the value back to the original plaintext
    when the row is read through SQLAlchemy.
    """
    plaintext = "5.8"
    lab = LabResult(
        patient_id=patient_row.id,
        kind=LabKind.fasting_glucose,
        value=plaintext,
        unit=LabUnit.mg_per_dl,
        sample_date=date.today(),
    )
    db_session.add(lab)
    await db_session.commit()

    await db_session.refresh(lab)
    assert lab.value == plaintext, (
        f"ORM must decrypt PHI column back to original value; got {lab.value!r}"
    )
