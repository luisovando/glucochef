"""Phase 9 — Suggestion endpoint.

POST /suggestions returns 3–4 nutritionally equivalent alternatives for a
given ingredient, respecting the patient's profile and rejected ingredients.
"""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.provider import AIProvider, Alternative
from app.core.config import settings
from app.core.security import get_current_patient
from app.db.session import get_db
from app.models.nutritional_profile import Allergy, DietaryPreference, Intolerance, NutritionalProfile
from app.models.patient import Patient
from app.models.rejected_ingredient import RejectedIngredient
from app.services.recommendations import build_clinical_context

router = APIRouter(prefix="/suggestions", tags=["suggestions"])


# ── Schemas ───────────────────────────────────────────────────────────────────


class SuggestionRequest(BaseModel):
    ingredient: str = Field(..., min_length=1, max_length=256)


class AlternativeResponse(BaseModel):
    ingredient: str
    rationale: str
    rank: int


class SuggestionResponse(BaseModel):
    ingredient: str
    alternatives: list[AlternativeResponse]


# ── Provider factory (patchable in tests) ─────────────────────────────────────


def get_ai_provider() -> AIProvider:
    """Return an AIProvider instance. Replaced by a mock in tests."""
    return AIProvider()


# ── Profile adapter ───────────────────────────────────────────────────────────


@dataclass
class _LoadedProfile:
    """Thin adapter satisfying the PatientProfile protocol."""

    diabetes_type: str
    allergies: list[str] | None
    intolerances: list[str] | None
    dietary_preferences: list[str] | None


async def _load_profile(
    patient: Patient, db: AsyncSession
) -> _LoadedProfile:
    """Load a patient's NutritionalProfile and associated PHI lists."""
    result = await db.execute(
        select(NutritionalProfile).where(
            NutritionalProfile.patient_id == patient.id
        )
    )
    profile = result.scalar_one_or_none()

    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Patient has no nutritional profile. Complete onboarding first.",
        )

    allergies_result = await db.execute(
        select(Allergy).where(Allergy.nutritional_profile_id == profile.id)
    )
    intolerances_result = await db.execute(
        select(Intolerance).where(Intolerance.nutritional_profile_id == profile.id)
    )
    prefs_result = await db.execute(
        select(DietaryPreference).where(
            DietaryPreference.nutritional_profile_id == profile.id
        )
    )

    allergies = [row.substance for row in allergies_result.scalars().all()]
    intolerances = [row.substance for row in intolerances_result.scalars().all()]
    preferences = [row.preference for row in prefs_result.scalars().all()]

    return _LoadedProfile(
        diabetes_type=profile.diabetes_type or "unknown",
        allergies=allergies or None,
        intolerances=intolerances or None,
        dietary_preferences=preferences or None,
    )


async def _load_rejected(patient: Patient, db: AsyncSession) -> list[str]:
    """Return the patient's normalised rejected ingredient list."""
    result = await db.execute(
        select(RejectedIngredient).where(
            RejectedIngredient.patient_id == patient.id
        )
    )
    return [row.ingredient_normalized for row in result.scalars().all()]


# ── Route ─────────────────────────────────────────────────────────────────────


@router.post("", response_model=SuggestionResponse)
async def suggest_alternatives(
    payload: SuggestionRequest,
    patient: Patient = Depends(get_current_patient),
    db: AsyncSession = Depends(get_db),
    provider: AIProvider = Depends(get_ai_provider),
) -> SuggestionResponse:
    """
    Return 3–4 nutritionally equivalent alternatives for the requested ingredient.

    - Respects the patient's allergies, intolerances, and dietary preferences.
    - Excludes previously rejected ingredients.
    - Raises HTTP 502 if the AI provider returns fewer than 3 alternatives
      after applying filters (do NOT silently pad).
    """
    profile = await _load_profile(patient, db)
    excluded = await _load_rejected(patient, db)
    # Build clinical context for diet-lab correlation (Phase 13).
    # Not yet forwarded to suggest_alternatives (provider signature unchanged per
    # Phase 9 do-not-change); available here for a future phase that extends the prompt.
    _clinical_context = await build_clinical_context(patient.id, db)

    alternatives: list[Alternative] = await provider.suggest_alternatives(
        ingredient=payload.ingredient,
        profile=profile,
        excluded=excluded,
    )

    if len(alternatives) < 3:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                f"AI provider returned only {len(alternatives)} alternative(s); "
                "at least 3 are required."
            ),
        )

    # Cap at 4 (provider prompt requests 3–4, but guard defensively)
    alternatives = alternatives[:4]

    return SuggestionResponse(
        ingredient=payload.ingredient,
        alternatives=[
            AlternativeResponse(
                ingredient=alt.ingredient,
                rationale=alt.rationale,
                rank=alt.rank,
            )
            for alt in alternatives
        ],
    )
