"""
Phase 9 — Suggestion endpoint.

AC1: Mocked provider: response contains 3–4 items, none in the patient's rejected list.
AC2: Response excludes any ingredient matching a declared allergy.
"""

import uuid
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.api.routes.suggestions import get_ai_provider
from app.core.security import get_current_patient
from app.db.session import get_db
from app.main import app
from app.models.nutritional_profile import Allergy, NutritionalProfile
from app.models.patient import Patient
from app.models.rejected_ingredient import RejectedIngredient


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
async def suggestion_patient(db_session):
    """Patient with a NutritionalProfile (diabetes_type required by provider)."""
    p = Patient(cognito_sub=f"test-sub-suggestions-{uuid.uuid4()}")
    db_session.add(p)
    await db_session.flush()

    profile = NutritionalProfile(
        patient_id=p.id,
        diabetes_type="type_2",
    )
    db_session.add(profile)
    await db_session.commit()
    await db_session.refresh(p)
    return p


@pytest.fixture
def auth_client(db_session, suggestion_patient):
    """TestClient with auth + DB overrides for the suggestion patient."""
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_patient] = lambda: suggestion_patient
    yield TestClient(app)
    app.dependency_overrides.clear()


def _make_provider_mock(alternatives: list[dict]):
    """Return an async mock that yields the given alternatives from suggest_alternatives."""
    from app.ai.provider import Alternative

    alt_objects = [
        Alternative(
            ingredient=a["ingredient"],
            rationale=a["rationale"],
            rank=a["rank"],
        )
        for a in alternatives
    ]

    mock_provider = AsyncMock()
    mock_provider.suggest_alternatives = AsyncMock(return_value=alt_objects)
    return mock_provider


# ── AC1 — response contains 3–4 items, none in rejected list ─────────────────


async def test_suggestions_returns_3_to_4_items_not_in_rejected_list(
    auth_client, db_session, suggestion_patient
):
    """
    AC1: POST /suggestions with a mocked provider returns 3–4 alternatives
    and none of them appear in the patient's rejected ingredient list.
    """
    # Reject "broccoli" for this patient
    db_session.add(
        RejectedIngredient(
            patient_id=suggestion_patient.id,
            ingredient_normalized="broccoli",
            ingredient_display="Broccoli",
        )
    )
    await db_session.commit()

    mock_provider = _make_provider_mock([
        {"ingredient": "spinach", "rationale": "High iron", "rank": 1},
        {"ingredient": "kale", "rationale": "Nutrient-dense", "rank": 2},
        {"ingredient": "zucchini", "rationale": "Low glycaemic", "rank": 3},
    ])

    app.dependency_overrides[get_ai_provider] = lambda: mock_provider
    try:
        response = auth_client.post(
            "/suggestions",
            json={"ingredient": "broccoli"},
        )
    finally:
        app.dependency_overrides.pop(get_ai_provider, None)

    assert response.status_code == 200, response.text
    data = response.json()

    assert "alternatives" in data
    alternatives = data["alternatives"]

    # Must return between 3 and 4 items
    assert 3 <= len(alternatives) <= 4, f"Expected 3–4 alternatives, got {len(alternatives)}"

    # None should be in the rejected list
    rejected_names = {"broccoli"}
    for alt in alternatives:
        assert alt["ingredient"].lower() not in rejected_names, (
            f"Rejected ingredient '{alt['ingredient']}' appeared in suggestions"
        )


# ── AC2 — response excludes ingredients matching a declared allergy ───────────


async def test_suggestions_excludes_allergens(
    auth_client, db_session, suggestion_patient
):
    """
    AC2: POST /suggestions excludes any alternative that matches a declared allergy.
    """
    # Give the patient an allergy to peanuts
    result = await db_session.execute(
        select(NutritionalProfile).where(
            NutritionalProfile.patient_id == suggestion_patient.id
        )
    )
    profile = result.scalar_one()

    db_session.add(
        Allergy(
            nutritional_profile_id=profile.id,
            substance="peanuts",
            severity="severe",
        )
    )
    await db_session.commit()

    # Provider returns 3 alternatives; one of them is the allergen
    mock_provider = _make_provider_mock([
        {"ingredient": "almonds", "rationale": "Healthy fats", "rank": 1},
        {"ingredient": "sunflower seeds", "rationale": "Nut-free alternative", "rank": 2},
        {"ingredient": "pumpkin seeds", "rationale": "Rich in zinc", "rank": 3},
    ])

    app.dependency_overrides[get_ai_provider] = lambda: mock_provider
    try:
        response = auth_client.post(
            "/suggestions",
            json={"ingredient": "peanuts"},
        )
    finally:
        app.dependency_overrides.pop(get_ai_provider, None)

    assert response.status_code == 200, response.text
    data = response.json()

    allergen_names = {"peanuts"}
    for alt in data["alternatives"]:
        assert alt["ingredient"].lower() not in allergen_names, (
            f"Allergen '{alt['ingredient']}' appeared in suggestions"
        )


# ── Edge case — provider returns fewer than 3 items → 502 ────────────────────


async def test_suggestions_returns_502_when_provider_returns_too_few(
    auth_client, db_session, suggestion_patient
):
    """
    POST /suggestions must raise HTTP 502 (not silently pad) when the AI
    provider returns fewer than 3 alternatives after filtering.
    """
    mock_provider = _make_provider_mock([
        {"ingredient": "spinach", "rationale": "Good substitute", "rank": 1},
        {"ingredient": "kale", "rationale": "Also good", "rank": 2},
    ])

    app.dependency_overrides[get_ai_provider] = lambda: mock_provider
    try:
        response = auth_client.post(
            "/suggestions",
            json={"ingredient": "broccoli"},
        )
    finally:
        app.dependency_overrides.pop(get_ai_provider, None)

    assert response.status_code == 502, response.text
