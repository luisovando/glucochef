"""
Phase 7 — Rejected ingredient persistence.

AC1: Rejecting "salmón" then rejecting "Salmón " (whitespace/case) results in a single row.
AC2: is_rejected returns True for the rejected ingredient and False otherwise.
"""

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.security import get_current_patient
from app.db.session import get_db
from app.main import app
from app.models.patient import Patient
from app.models.rejected_ingredient import RejectedIngredient
from app.repositories.rejected_ingredient import RejectedIngredientRepository


@pytest.fixture
async def ingredient_patient(db_session):
    """Insert a Patient row to be used as the authenticated user."""
    p = Patient(cognito_sub=f"test-sub-ingredients-{uuid.uuid4()}")
    db_session.add(p)
    await db_session.commit()
    await db_session.refresh(p)
    return p


@pytest.fixture
def auth_client(db_session, ingredient_patient):
    """TestClient with auth + DB overrides for the ingredient patient."""
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_patient] = lambda: ingredient_patient
    client = TestClient(app)
    try:
        yield client
    finally:
        app.dependency_overrides.clear()


async def test_duplicate_rejection_normalized_to_single_row(auth_client, db_session, ingredient_patient):
    """
    AC1 — Rejecting "salmón" then "Salmón " (whitespace/case variant) must result
    in exactly one row in rejected_ingredients for this patient.
    """
    r1 = auth_client.post("/ingredients/salmón/reject")
    assert r1.status_code == 200, r1.text

    r2 = auth_client.post("/ingredients/Salmón%20/reject")
    assert r2.status_code == 200, r2.text

    result = await db_session.execute(
        select(RejectedIngredient).where(
            RejectedIngredient.patient_id == ingredient_patient.id
        )
    )
    rows = result.scalars().all()
    assert len(rows) == 1, f"Expected 1 row, got {len(rows)}"


async def test_is_rejected_returns_true_and_false(db_session, ingredient_patient):
    """
    AC2 — is_rejected returns True for a rejected ingredient and False otherwise.
    """
    repo = RejectedIngredientRepository(db_session)

    await repo.reject(ingredient_patient.id, "tofu")
    await db_session.commit()

    assert await repo.is_rejected(ingredient_patient.id, "tofu") is True
    assert await repo.is_rejected(ingredient_patient.id, "chicken") is False
