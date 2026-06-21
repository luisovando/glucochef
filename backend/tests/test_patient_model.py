"""Phase 3 AC: Pytest fixture can insert a Patient row."""
import pytest
from sqlalchemy import select

from app.models.patient import Patient


@pytest.mark.asyncio
async def test_insert_patient(db_session):
    patient = Patient(
        cognito_sub="test-sub-001",
        display_name="Test Patient",
        consent_accepted=True,
    )
    db_session.add(patient)
    await db_session.commit()
    await db_session.refresh(patient)

    result = await db_session.execute(select(Patient).where(Patient.cognito_sub == "test-sub-001"))
    fetched = result.scalar_one()

    assert fetched.id is not None
    assert fetched.cognito_sub == "test-sub-001"
    assert fetched.consent_accepted is True
