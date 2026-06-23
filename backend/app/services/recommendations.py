"""
Phase 13 — Diet–clinical correlation.

build_clinical_context(patient_id, session) returns a small dict of the form
  {"hba1c": "green"|"amber"|"red", "fasting_glucose": ..., ...}
consumed by AIProvider.suggest_alternatives and AIProvider.generate_recipe.

The dict contains only traffic-light status strings — no raw PHI values —
so it is safe to pass to the AI provider per the HIPAA alignment rules.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import LabKind
from app.models.lab_result import LabResult
from app.services.labs import evaluate

# ── Module-level constant used in prompts and assertions ─────────────────────
# This exact string is injected into the AI prompt when HbA1c is red.
# Tests assert its presence / absence to verify the wiring.

CARB_LIMIT_PHRASE = "limit refined carbs"


async def build_clinical_context(
    patient_id: uuid.UUID,
    session: AsyncSession,
) -> dict[str, str]:
    """
    Return a dict mapping each lab kind to its latest traffic-light status.

    Only lab kinds that have at least one result are included. If a patient
    has no lab results yet, an empty dict is returned (equivalent to
    latest_labs=None for the AI provider).

    Example output:
      {"hba1c": "red", "fasting_glucose": "amber"}
    """
    # Fetch all lab results for the patient, ordered by date descending so we
    # can pick the most recent value per kind.
    result = await session.execute(
        select(LabResult)
        .where(LabResult.patient_id == patient_id)
        .order_by(LabResult.kind.asc(), LabResult.sample_date.desc())
    )
    all_labs = result.scalars().all()

    # Keep only the most recent result per kind
    latest: dict[str, str] = {}
    seen_kinds: set[LabKind] = set()
    for lab in all_labs:
        if lab.kind not in seen_kinds:
            seen_kinds.add(lab.kind)
            latest[lab.kind.value] = evaluate(lab.value, lab.kind)

    return latest
