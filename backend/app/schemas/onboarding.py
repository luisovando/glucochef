import uuid
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class MedicationRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=256)
    dosage: Optional[str] = Field(None, max_length=256)


class AllergyRequest(BaseModel):
    substance: str = Field(..., min_length=1, max_length=256)
    severity: Optional[str] = Field(None, max_length=64)


class OnboardingRequest(BaseModel):
    diabetes_type: str = Field(..., min_length=1, max_length=64)
    diagnosis_date: Optional[str] = Field(None, max_length=32)
    additional_notes: Optional[str] = Field(None, max_length=2048)
    medications: list[MedicationRequest] = []
    allergies: list[AllergyRequest] = []
    intolerances: list[str] = []
    rejected_foods: list[str] = []
    cultural_preferences: list[str] = []
    consent: bool

    @field_validator("consent")
    @classmethod
    def consent_must_be_true(cls, v: bool) -> bool:
        if not v:
            raise ValueError("Explicit consent is required to store health data")
        return v


class OnboardingResponse(BaseModel):
    profile_id: uuid.UUID
