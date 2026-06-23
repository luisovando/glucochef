import uuid
from typing import Optional

from pydantic import BaseModel, Field, field_validator


def _strip_required(value: str, field_name: str) -> str:
    value = value.strip()
    if value == "":
        raise ValueError(f"{field_name} cannot be empty or whitespace-only")
    return value


class MedicationRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=256)
    dosage: Optional[str] = Field(None, max_length=256)

    @field_validator("name")
    @classmethod
    def name_must_be_meaningful(cls, v: str) -> str:
        return _strip_required(v, "Medication name")

    @field_validator("dosage")
    @classmethod
    def dosage_must_be_meaningful_or_none(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        return v if v else None


class AllergyRequest(BaseModel):
    substance: str = Field(..., min_length=1, max_length=256)
    severity: Optional[str] = Field(None, max_length=64)

    @field_validator("substance")
    @classmethod
    def substance_must_be_meaningful(cls, v: str) -> str:
        return _strip_required(v, "Allergy substance")

    @field_validator("severity")
    @classmethod
    def severity_must_be_meaningful_or_none(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        return v if v else None


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

    @field_validator("diabetes_type")
    @classmethod
    def diabetes_type_must_be_meaningful(cls, v: str) -> str:
        return _strip_required(v, "Diabetes type")

    @field_validator("diagnosis_date")
    @classmethod
    def diagnosis_date_must_be_meaningful_or_none(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        return v if v else None

    @field_validator("additional_notes")
    @classmethod
    def additional_notes_must_be_meaningful_or_none(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        return v if v else None

    @field_validator("intolerances", "rejected_foods", "cultural_preferences")
    @classmethod
    def strip_list_items(cls, v: list[str]) -> list[str]:
        return [item.strip() for item in v if item.strip()]

    @field_validator("consent")
    @classmethod
    def consent_must_be_true(cls, v: bool) -> bool:
        if not v:
            raise ValueError("Explicit consent is required to store health data")
        return v


class OnboardingResponse(BaseModel):
    profile_id: uuid.UUID
