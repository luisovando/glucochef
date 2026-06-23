"""Pydantic schemas for the lab registration endpoint (Phase 11)."""

import uuid
from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.models.enums import LabKind, LabUnit

# ── Valid numeric ranges per lab kind ────────────────────────────────────────
# Sources: ADA guidelines and standard clinical reference ranges.

_RANGES: dict[str, tuple[float, float]] = {
    # HbA1c in percent: 3–20 per PRD
    LabKind.hba1c: (3.0, 20.0),
    # Fasting glucose in mg/dL: physiologically plausible range 1–1000
    LabKind.fasting_glucose: (1.0, 1000.0),
    # Total cholesterol in mg/dL: 1–999
    LabKind.total_cholesterol: (1.0, 999.0),
    # Triglycerides in mg/dL: 1–5000
    LabKind.triglycerides: (1.0, 5000.0),
}


class LabCreateRequest(BaseModel):
    kind: LabKind
    value: str = Field(..., min_length=1, max_length=32)
    unit: LabUnit
    sample_date: date

    @field_validator("value")
    @classmethod
    def value_within_clinical_range(cls, v: str, info) -> str:
        """Validate that the numeric value falls within the clinical range for its kind."""
        # Access the sibling field via info.data (populated in validation order)
        kind = info.data.get("kind")
        if kind is None:
            # kind failed validation earlier; skip range check
            return v

        try:
            numeric = float(v)
        except ValueError:
            raise ValueError(f"Lab value must be a number, got: {v!r}")

        lo, hi = _RANGES.get(kind, (float("-inf"), float("inf")))
        if not (lo <= numeric <= hi):
            raise ValueError(
                f"{kind} value {numeric} is out of the valid range [{lo}, {hi}]"
            )
        return v


class LabCreateResponse(BaseModel):
    lab_id: str
