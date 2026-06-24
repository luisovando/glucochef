"""
Phase 11 — Lab registration endpoint.

AC1: Valid payload → 201; out-of-range payload → 422.
AC2: Stored value round-trips through encryption.
"""

import uuid
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, text

from app.core.security import get_current_patient
from app.db.session import get_db
from app.main import app
from app.models.enums import LabKind, LabUnit
from app.models.lab_result import LabResult
from app.models.patient import Patient


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
async def lab_patient(db_session):
    """Patient row for lab tests."""
    p = Patient(cognito_sub=f"test-sub-labs-{uuid.uuid4()}")
    db_session.add(p)
    await db_session.commit()
    await db_session.refresh(p)
    return p


@pytest.fixture
def auth_client(db_session, lab_patient):
    """TestClient with auth + DB overrides for the lab patient."""
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_patient] = lambda: lab_patient
    yield TestClient(app)
    app.dependency_overrides.clear()


# ── AC1a — valid payload returns 201 ─────────────────────────────────────────


async def test_valid_lab_payload_returns_201(auth_client):
    """AC1a: POST /labs with a valid HbA1c payload returns HTTP 201."""
    response = auth_client.post(
        "/labs",
        json={
            "kind": "hba1c",
            "value": "7.2",
            "unit": "percent",
            "sample_date": str(date.today()),
        },
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert "lab_id" in data


async def test_valid_fasting_glucose_returns_201(auth_client):
    """AC1a: POST /labs with a valid fasting glucose payload returns 201."""
    response = auth_client.post(
        "/labs",
        json={
            "kind": "fasting_glucose",
            "value": "95",
            "unit": "mg_per_dl",
            "sample_date": str(date.today()),
        },
    )
    assert response.status_code == 201, response.text


async def test_valid_total_cholesterol_returns_201(auth_client):
    """AC1a: POST /labs with a valid total cholesterol payload returns 201."""
    response = auth_client.post(
        "/labs",
        json={
            "kind": "total_cholesterol",
            "value": "180",
            "unit": "mg_per_dl",
            "sample_date": str(date.today()),
        },
    )
    assert response.status_code == 201, response.text


async def test_valid_triglycerides_returns_201(auth_client):
    """AC1a: POST /labs with a valid triglycerides payload returns 201."""
    response = auth_client.post(
        "/labs",
        json={
            "kind": "triglycerides",
            "value": "130",
            "unit": "mg_per_dl",
            "sample_date": str(date.today()),
        },
    )
    assert response.status_code == 201, response.text


# ── AC1b — out-of-range payload returns 422 ───────────────────────────────────


async def test_hba1c_below_minimum_returns_422(auth_client):
    """AC1b: HbA1c below 3% (lower valid bound) returns 422."""
    response = auth_client.post(
        "/labs",
        json={
            "kind": "hba1c",
            "value": "2.9",
            "unit": "percent",
            "sample_date": str(date.today()),
        },
    )
    assert response.status_code == 422, response.text


async def test_hba1c_above_maximum_returns_422(auth_client):
    """AC1b: HbA1c above 20% (upper valid bound) returns 422."""
    response = auth_client.post(
        "/labs",
        json={
            "kind": "hba1c",
            "value": "20.1",
            "unit": "percent",
            "sample_date": str(date.today()),
        },
    )
    assert response.status_code == 422, response.text


async def test_fasting_glucose_out_of_range_returns_422(auth_client):
    """AC1b: Fasting glucose value of 0 is out of range → 422."""
    response = auth_client.post(
        "/labs",
        json={
            "kind": "fasting_glucose",
            "value": "0",
            "unit": "mg_per_dl",
            "sample_date": str(date.today()),
        },
    )
    assert response.status_code == 422, response.text


# ── AC2 — stored value round-trips through encryption ────────────────────────


async def test_lab_value_round_trips_through_encryption(auth_client, db_session, lab_patient):
    """
    AC2: The value submitted via POST /labs is stored encrypted at rest and
    decrypts back to the original plaintext when read through the ORM.
    """
    plaintext = "6.5"

    response = auth_client.post(
        "/labs",
        json={
            "kind": "hba1c",
            "value": plaintext,
            "unit": "percent",
            "sample_date": str(date.today()),
        },
    )
    assert response.status_code == 201, response.text
    lab_id = response.json()["lab_id"]

    # Read the raw bytes stored in the column (bypass ORM type system)
    raw_result = await db_session.execute(
        text("SELECT value FROM lab_results WHERE id = :id"),
        {"id": lab_id},
    )
    raw_value = raw_result.scalar()
    assert raw_value != plaintext, (
        f"PHI value must be stored as ciphertext, found plaintext: {raw_value!r}"
    )

    # Read through ORM — must decrypt back to original plaintext
    orm_result = await db_session.execute(
        select(LabResult).where(LabResult.id == uuid.UUID(lab_id))
    )
    lab = orm_result.scalar_one()
    assert lab.value == plaintext, (
        f"ORM must decrypt to original value; got {lab.value!r}"
    )
