from datetime import date

from datetime import date

from fastapi import APIRouter, Depends, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import audit
from app.core.security import get_current_patient
from app.db.session import get_db
from app.models.enums import AuditAction, AuditResource
from app.models.nutritional_profile import (
    Allergy,
    DietaryPreference,
    Intolerance,
    Medication,
    NutritionalProfile,
)
from app.models.patient import Patient
from app.models.rejected_ingredient import RejectedIngredient
from app.schemas.onboarding import OnboardingRequest, OnboardingResponse

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_profile(
    payload: OnboardingRequest,
    patient: Patient = Depends(get_current_patient),
    db: AsyncSession = Depends(get_db),
) -> OnboardingResponse:
    """
    Create or update the authenticated patient's NutritionalProfile.

    This endpoint is protected by Cognito JWT verification and audited.
    Explicit consent is required (enforced by the request schema). A second
    submission for the same patient updates the existing profile instead of
    creating a duplicate.
    """
    # Upsert the NutritionalProfile row for the authenticated patient.
    result = await db.execute(
        select(NutritionalProfile).where(
            NutritionalProfile.patient_id == patient.id
        )
    )
    profile = result.scalar_one_or_none()

    if profile is None:
        profile = NutritionalProfile(patient_id=patient.id)
        db.add(profile)
    else:
        # Replace related rows explicitly; avoid lazy-loading collections.
        await db.execute(
            delete(Medication).where(
                Medication.nutritional_profile_id == profile.id
            )
        )
        await db.execute(
            delete(Allergy).where(Allergy.nutritional_profile_id == profile.id)
        )
        await db.execute(
            delete(Intolerance).where(
                Intolerance.nutritional_profile_id == profile.id
            )
        )
        await db.execute(
            delete(DietaryPreference).where(
                DietaryPreference.nutritional_profile_id == profile.id
            )
        )

    profile.diabetes_type = payload.diabetes_type
    profile.diagnosis_date = payload.diagnosis_date
    profile.additional_notes = payload.additional_notes

    await db.flush()

    # Populate related PHI rows using explicit foreign keys.
    for medication in payload.medications:
        db.add(
            Medication(
                nutritional_profile_id=profile.id,
                name=medication.name,
                dosage=medication.dosage,
            )
        )

    for allergy in payload.allergies:
        db.add(
            Allergy(
                nutritional_profile_id=profile.id,
                substance=allergy.substance,
                severity=allergy.severity,
            )
        )

    for substance in payload.intolerances:
        db.add(
            Intolerance(
                nutritional_profile_id=profile.id,
                substance=substance,
            )
        )

    for preference in payload.cultural_preferences:
        db.add(
            DietaryPreference(
                nutritional_profile_id=profile.id,
                preference=preference,
            )
        )

    # Replace rejected ingredients (not part of NutritionalProfile cascade).
    await db.execute(
        delete(RejectedIngredient).where(
            RejectedIngredient.patient_id == patient.id
        )
    )
    for ingredient in payload.rejected_foods:
        normalized = ingredient.strip().lower()
        db.add(
            RejectedIngredient(
                patient_id=patient.id,
                ingredient_normalized=normalized,
                ingredient_display=ingredient.strip(),
            )
        )

    # Record explicit consent on the patient record.
    patient.consent_accepted = True
    patient.consent_accepted_on = date.today()

    await db.flush()
    await db.refresh(profile)

    # Audit the PHI write and the consent inside the same transaction.
    async with audit(
        session=db,
        actor=patient,
        action=AuditAction.write,
        resource=AuditResource.onboarding,
        resource_id=profile.id,
    ):
        pass

    async with audit(
        session=db,
        actor=patient,
        action=AuditAction.consent,
        resource=AuditResource.onboarding,
        resource_id=profile.id,
    ):
        pass

    await db.commit()

    return OnboardingResponse(profile_id=profile.id)
