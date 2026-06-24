"""
Phase 10 — Recipe generation endpoint.

AC1: Response includes title, ingredients, steps, nutrition_summary.
AC2: When latest_labs shows red-flag HbA1c, the prompt sent to the provider
     includes a tightened carb constraint (assert on the captured prompt).
"""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.routes.recipes import get_ai_provider
from app.core.security import get_current_patient
from app.db.session import get_db
from app.main import app
from app.models.nutritional_profile import NutritionalProfile
from app.models.patient import Patient


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
async def recipe_patient(db_session):
    """Patient with a NutritionalProfile."""
    p = Patient(cognito_sub=f"test-sub-recipes-{uuid.uuid4()}")
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
def auth_client(db_session, recipe_patient):
    """TestClient with auth + DB overrides for the recipe patient."""
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_patient] = lambda: recipe_patient
    yield TestClient(app)
    app.dependency_overrides.clear()


def _mock_provider_returning(recipe_dict: dict):
    """Return an async mock that yields recipe_dict from generate_recipe."""
    mock = AsyncMock()
    mock.generate_recipe = AsyncMock(return_value=recipe_dict)
    return mock


# ── AC1 — response includes required fields ───────────────────────────────────


async def test_recipe_response_includes_required_fields(auth_client, recipe_patient):
    """
    AC1: POST /recipes returns a body with title, ingredients, steps,
    and nutrition_summary.
    """
    mock_provider = _mock_provider_returning({
        "title": "Grilled Chicken Bowl",
        "ingredients": ["chicken breast", "rice", "broccoli"],
        "instructions": ["Season the chicken.", "Grill for 10 min.", "Serve with rice."],
        "servings": 2,
        "prep_time_minutes": 20,
        "nutrition_summary": {"carbs": "45g", "protein": "30g", "fat": "10g"},
    })

    app.dependency_overrides[get_ai_provider] = lambda: mock_provider
    try:
        response = auth_client.post(
            "/recipes",
            json={"accepted_ingredients": ["chicken breast", "rice", "broccoli"]},
        )
    finally:
        app.dependency_overrides.pop(get_ai_provider, None)

    assert response.status_code == 201, response.text
    data = response.json()

    assert "title" in data, "Response must include 'title'"
    assert "ingredients" in data, "Response must include 'ingredients'"
    assert "steps" in data, "Response must include 'steps'"
    assert "nutrition_summary" in data, "Response must include 'nutrition_summary'"


# ── AC2 — red HbA1c tightens carb constraint in prompt ───────────────────────


async def test_red_hba1c_adds_carb_constraint_to_prompt(auth_client, recipe_patient):
    """
    AC2: When latest_labs contains hba1c: red, the prompt sent to the provider
    must include a tightened carb constraint phrase.
    """
    from app.ai.provider import _build_recipe_prompt
    from dataclasses import dataclass

    @dataclass
    class FakeProfile:
        diabetes_type: str = "type_2"
        allergies: list = None
        intolerances: list = None
        dietary_preferences: list = None

    profile = FakeProfile()
    latest_labs = {"hba1c": "red"}

    messages = _build_recipe_prompt(
        accepted_ingredients=["rice", "chicken"],
        profile=profile,
        latest_labs=latest_labs,
    )

    prompt_text = " ".join(
        m["content"] for m in messages if isinstance(m.get("content"), str)
    )

    # The prompt must contain a carb-restriction signal when HbA1c is red
    carb_keywords = ["carb", "carbohydrate", "low-carb", "restrict"]
    assert any(kw in prompt_text.lower() for kw in carb_keywords), (
        f"Prompt must include a carb constraint when HbA1c is red. Got:\n{prompt_text}"
    )
