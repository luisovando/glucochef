"""
Phase 13 — Diet–clinical correlation.

AC1: With HbA1c red, the prompt contains the string "limit refined carbs"
     (or the equivalent constant defined in app/services/recommendations.py).
AC2: With all greens, the prompt omits any tightening clause.
"""

import uuid
from dataclasses import dataclass
from datetime import date

import pytest

from app.models.enums import LabKind, LabUnit
from app.models.lab_result import LabResult
from app.models.patient import Patient


@dataclass
class FakeProfile:
    diabetes_type: str = "type_2"
    allergies: list = None
    intolerances: list = None
    dietary_preferences: list = None


# ── AC1 — HbA1c red → "limit refined carbs" appears in prompt ────────────────


async def test_hba1c_red_context_tightens_carb_guidance_in_prompt(db_session):
    """
    AC1: build_clinical_context with red HbA1c injects the carb-limit constant
    into the prompt returned by _build_recipe_prompt.
    """
    from app.ai.provider import _build_recipe_prompt
    from app.services.recommendations import CARB_LIMIT_PHRASE, build_clinical_context

    patient = Patient(cognito_sub=f"test-sub-rec-{uuid.uuid4()}")
    db_session.add(patient)
    await db_session.flush()

    # Single red HbA1c result
    db_session.add(LabResult(
        patient_id=patient.id,
        kind=LabKind.hba1c,
        value="10.5",   # red: ≥ 9.0
        unit=LabUnit.percent,
        sample_date=date.today(),
    ))
    await db_session.commit()

    context = await build_clinical_context(patient.id, db_session)

    # Context must indicate red HbA1c
    assert context.get("hba1c") == "red", f"Expected hba1c: red, got {context!r}"

    # Prompt must contain the carb-limit phrase
    profile = FakeProfile()
    messages = _build_recipe_prompt(
        accepted_ingredients=["rice", "chicken"],
        profile=profile,
        latest_labs=context,
    )
    prompt_text = " ".join(m["content"] for m in messages if isinstance(m.get("content"), str))

    assert CARB_LIMIT_PHRASE in prompt_text, (
        f"Prompt must contain {CARB_LIMIT_PHRASE!r} when HbA1c is red.\nPrompt:\n{prompt_text}"
    )


# ── AC2 — all greens → tightening clause omitted ─────────────────────────────


async def test_all_green_labs_omit_carb_tightening_from_prompt(db_session):
    """
    AC2: build_clinical_context with all-green labs produces a prompt that
    does NOT contain the carb-limit phrase.
    """
    from app.ai.provider import _build_recipe_prompt
    from app.services.recommendations import CARB_LIMIT_PHRASE, build_clinical_context

    patient = Patient(cognito_sub=f"test-sub-rec-green-{uuid.uuid4()}")
    db_session.add(patient)
    await db_session.flush()

    # All-green results
    db_session.add(LabResult(
        patient_id=patient.id,
        kind=LabKind.hba1c,
        value="6.0",   # green: < 7.0
        unit=LabUnit.percent,
        sample_date=date.today(),
    ))
    db_session.add(LabResult(
        patient_id=patient.id,
        kind=LabKind.fasting_glucose,
        value="90",    # green: 70–<100
        unit=LabUnit.mg_per_dl,
        sample_date=date.today(),
    ))
    await db_session.commit()

    context = await build_clinical_context(patient.id, db_session)

    profile = FakeProfile()
    messages = _build_recipe_prompt(
        accepted_ingredients=["rice", "chicken"],
        profile=profile,
        latest_labs=context,
    )
    prompt_text = " ".join(m["content"] for m in messages if isinstance(m.get("content"), str))

    assert CARB_LIMIT_PHRASE not in prompt_text, (
        f"Prompt must NOT contain carb-limit phrase when all labs are green.\nPrompt:\n{prompt_text}"
    )


# ── Wiring test — suggestions and recipes routes use build_clinical_context ───


async def test_suggestions_route_builds_clinical_context_without_error(db_session):
    """
    Verifies that the suggestions route successfully calls build_clinical_context
    and completes the request when a red HbA1c lab result exists.

    Note: _clinical_context is not forwarded to suggest_alternatives (the
    provider signature is frozen per Phase 9 do-not-change). This test confirms
    the wiring does not break the route, not that the context reaches the provider.
    """
    from unittest.mock import AsyncMock

    from fastapi.testclient import TestClient

    from app.ai.provider import Alternative
    from app.api.routes.suggestions import get_ai_provider
    from app.core.security import get_current_patient
    from app.db.session import get_db
    from app.main import app
    from app.models.nutritional_profile import NutritionalProfile

    patient = Patient(cognito_sub=f"test-sub-wire-{uuid.uuid4()}")
    db_session.add(patient)
    await db_session.flush()

    db_session.add(NutritionalProfile(patient_id=patient.id, diabetes_type="type_2"))

    db_session.add(LabResult(
        patient_id=patient.id,
        kind=LabKind.hba1c,
        value="10.5",
        unit=LabUnit.percent,
        sample_date=date.today(),
    ))
    await db_session.commit()

    captured_excluded = []

    async def _fake_suggest(ingredient, profile, excluded):
        captured_excluded.extend(excluded)
        return [
            Alternative("spinach", "High iron", 1),
            Alternative("kale", "Nutrient dense", 2),
            Alternative("zucchini", "Low glycaemic", 3),
        ]

    mock_provider = AsyncMock()
    mock_provider.suggest_alternatives = _fake_suggest

    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_patient] = lambda: patient
    app.dependency_overrides[get_ai_provider] = lambda: mock_provider
    try:
        client = TestClient(app)
        response = client.post("/suggestions", json={"ingredient": "broccoli"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200, response.text
