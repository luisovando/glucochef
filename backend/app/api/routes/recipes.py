"""Phase 10 — Recipe generation endpoint.

POST /recipes builds a recipe from accepted ingredients and the latest labs,
persists the resulting Recipe linked to the patient, and returns it.

Soft dependency on Phase 11 (lab registration): if no labs exist yet for the
patient, latest_labs is passed as None to the provider.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.provider import AIProvider
from app.api.routes.suggestions import _load_profile
from app.core.security import get_current_patient
from app.db.session import get_db
from app.models.patient import Patient
from app.models.recipe import Recipe

router = APIRouter(prefix="/recipes", tags=["recipes"])


# ── Schemas ───────────────────────────────────────────────────────────────────


class RecipeRequest(BaseModel):
    accepted_ingredients: list[str] = Field(..., min_length=1)


class RecipeResponse(BaseModel):
    recipe_id: str
    title: str
    ingredients: list
    steps: list
    nutrition_summary: dict | None = None


# ── Provider factory (patchable in tests) ─────────────────────────────────────


def get_ai_provider() -> AIProvider:
    """Return an AIProvider instance. Replaced by a mock in tests."""
    return AIProvider()


# ── Route ─────────────────────────────────────────────────────────────────────


@router.post("", response_model=RecipeResponse, status_code=status.HTTP_201_CREATED)
async def generate_recipe(
    payload: RecipeRequest,
    patient: Patient = Depends(get_current_patient),
    db: AsyncSession = Depends(get_db),
    provider: AIProvider = Depends(get_ai_provider),
) -> RecipeResponse:
    """
    Generate a recipe from the accepted ingredients and (optionally) the latest
    lab results, then persist it linked to the patient.

    - latest_labs is passed as None when no lab results exist yet (soft dep Phase 11).
    - The provider prompt includes a tightened carb constraint when HbA1c is red.
    """
    profile = await _load_profile(patient, db)

    # Soft dependency on Phase 11 — pass None until labs are available.
    latest_labs: dict[str, str] | None = None

    raw: dict = await provider.generate_recipe(
        accepted_ingredients=payload.accepted_ingredients,
        profile=profile,
        latest_labs=latest_labs,
    )

    recipe = Recipe(
        patient_id=patient.id,
        title=raw.get("title", "Untitled Recipe"),
        content=raw,
        clinical_context_summary=latest_labs,
    )
    db.add(recipe)
    await db.commit()
    await db.refresh(recipe)

    return RecipeResponse(
        recipe_id=str(recipe.id),
        title=raw.get("title", ""),
        ingredients=raw.get("ingredients", []),
        steps=raw.get("instructions", []),
        nutrition_summary=raw.get("nutrition_summary"),
    )
