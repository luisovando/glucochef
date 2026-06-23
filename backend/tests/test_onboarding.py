"""
Phase 6 — Onboarding API.

AC1: authenticated POST creates a profile and returns 201 with the profile id.
AC2: unauthenticated POST returns 401.
AC3: posting twice for the same patient updates (does not duplicate) the profile.
"""

import uuid
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.session import get_db
from app.core.security import get_current_patient
from app.main import app
from app.models.nutritional_profile import NutritionalProfile
from app.models.patient import Patient


@pytest.fixture
async def onboarding_patient(db_session):
    """Insert a Patient row to be used as the authenticated user."""
    p = Patient(
        cognito_sub=f"test-sub-onboarding-{uuid.uuid4()}",
        consent_accepted=True,
        consent_accepted_on=date.today(),
    )
    db_session.add(p)
    await db_session.commit()
    await db_session.refresh(p)
    return p


@pytest.fixture
def auth_client(db_session, onboarding_patient):
    """TestClient with auth + DB overrides for the onboarding patient."""
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_patient] = lambda: onboarding_patient
    client = TestClient(app)
    try:
        yield client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def no_auth_client(db_session):
    """TestClient with DB override but no auth override."""
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)
    try:
        yield client
    finally:
        app.dependency_overrides.clear()


def _valid_payload():
    return {
        "diabetes_type": "type2",
        "diagnosis_date": "2020-01-15",
        "medications": [{"name": "Metformin", "dosage": "500mg"}],
        "allergies": [{"substance": "Peanuts", "severity": "severe"}],
        "intolerances": ["Lactose"],
        "rejected_foods": ["Salmon", "Tofu"],
        "cultural_preferences": ["Mediterranean", "low-sodium"],
        "consent": True,
    }


async def test_authenticated_post_creates_profile(auth_client, db_session, onboarding_patient):
    """
    AC1 — Authenticated POST /onboarding creates a NutritionalProfile and
    returns HTTP 201 with the profile id.
    """
    payload = _valid_payload()
    response = auth_client.post("/onboarding", json=payload)

    assert response.status_code == 201, response.text
    data = response.json()
    assert "profile_id" in data
    profile_id = uuid.UUID(data["profile_id"])

    result = await db_session.execute(
        select(NutritionalProfile).where(NutritionalProfile.patient_id == onboarding_patient.id)
    )
    profile = result.scalar_one_or_none()
    assert profile is not None
    assert profile.id == profile_id
    assert profile.diabetes_type == "type2"


async def test_unauthenticated_post_returns_401(no_auth_client):
    """
    AC2 — POST /onboarding without a valid Authorization header returns 401.
    """
    payload = _valid_payload()
    response = no_auth_client.post("/onboarding", json=payload)
    assert response.status_code == 401


async def test_posting_twice_updates_profile(auth_client, db_session, onboarding_patient):
    """
    AC3 — Posting onboarding twice for the same patient updates the existing
    NutritionalProfile instead of creating a duplicate.
    """
    payload = _valid_payload()
    first = auth_client.post("/onboarding", json=payload)
    assert first.status_code == 201
    first_id = uuid.UUID(first.json()["profile_id"])

    payload["diabetes_type"] = "type1"
    payload["medications"] = [{"name": "Insulin", "dosage": "10 units"}]
    second = auth_client.post("/onboarding", json=payload)
    assert second.status_code == 201
    second_id = uuid.UUID(second.json()["profile_id"])

    assert first_id == second_id

    result = await db_session.execute(
        select(NutritionalProfile).where(NutritionalProfile.patient_id == onboarding_patient.id)
    )
    profiles = result.scalars().all()
    assert len(profiles) == 1
    assert profiles[0].diabetes_type == "type1"
