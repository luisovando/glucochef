"""
Phase 12 — Traffic-light evaluation and trend computation for lab results.

Public API:
  evaluate(value: str, kind: LabKind) -> Literal["green", "amber", "red"]
  compute_trend(patient_id, kind, session) -> Literal["improving", "stable", "worsening"]

Thresholds are sourced from ADA (American Diabetes Association) guidelines
and standard clinical reference ranges.

  HbA1c (%):
    green  < 7.0   — well-controlled
    amber  7.0–<9.0 — suboptimal; warrants review
    red   ≥ 9.0   — poor control; prompt clinical attention

  Fasting plasma glucose (mg/dL):
    green  70–<100   — normal
    amber  100–<126  — pre-diabetes range (IFG)
    red    < 70      — hypoglycaemia
    red   ≥ 126      — diabetes diagnostic threshold

  Total cholesterol (mg/dL):
    green  < 200     — desirable
    amber  200–<240  — borderline high
    red   ≥ 240      — high

  Triglycerides (mg/dL):
    green  < 150     — normal
    amber  150–<200  — borderline high
    red   ≥ 200      — high
"""

from __future__ import annotations

import uuid
from typing import Literal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import LabKind
from app.models.lab_result import LabResult

Status = Literal["green", "amber", "red"]
Trend = Literal["improving", "stable", "worsening"]


# ── Threshold tables ──────────────────────────────────────────────────────────
# Each entry: (lower_bound_inclusive, upper_bound_exclusive, status)
# Evaluated in order; first match wins.

_THRESHOLDS: dict[LabKind, list[tuple[float, float, Status]]] = {
    LabKind.hba1c: [
        (0.0, 7.0, "green"),
        (7.0, 9.0, "amber"),
        (9.0, float("inf"), "red"),
    ],
    LabKind.fasting_glucose: [
        (0.0, 70.0, "red"),       # hypoglycaemia
        (70.0, 100.0, "green"),
        (100.0, 126.0, "amber"),
        (126.0, float("inf"), "red"),
    ],
    LabKind.total_cholesterol: [
        (0.0, 200.0, "green"),
        (200.0, 240.0, "amber"),
        (240.0, float("inf"), "red"),
    ],
    LabKind.triglycerides: [
        (0.0, 150.0, "green"),
        (150.0, 200.0, "amber"),
        (200.0, float("inf"), "red"),
    ],
}


def evaluate(value: str, kind: LabKind) -> Status:
    """
    Return the traffic-light status for a single lab value.

    Args:
        value: The lab value as a string (stored encrypted; passed decrypted here).
        kind:  The lab type (LabKind enum).

    Returns:
        "green", "amber", or "red" per ADA thresholds.

    Raises:
        ValueError: If value cannot be parsed as a float or kind is unknown.
    """
    numeric = float(value)

    thresholds = _THRESHOLDS.get(kind)
    if thresholds is None:
        raise ValueError(f"Unknown lab kind: {kind!r}")

    for lo, hi, status in thresholds:
        if lo <= numeric < hi:
            return status

    # Should be unreachable for valid ranges, but default to red for safety.
    return "red"  # pragma: no cover


# ── Trend computation ─────────────────────────────────────────────────────────


async def compute_trend(
    patient_id: uuid.UUID,
    kind: LabKind,
    session: AsyncSession,
) -> Trend:
    """
    Compute the trend (improving | stable | worsening) over the latest 3
    entries of the given lab kind for the patient.

    Logic:
      - Fetch the 3 most recent rows ordered by sample_date ascending.
      - If fewer than 2 entries exist, return "stable" (no trend possible).
      - Compare status ordinal of each consecutive pair:
          ordinal: green=0, amber=1, red=2
      - If each step is strictly higher → worsening
      - If each step is strictly lower  → improving
      - Otherwise                       → stable

    Only the traffic-light status (not the raw numeric value) is used for
    trend direction to avoid PHI leakage in comparisons.
    """
    result = await session.execute(
        select(LabResult)
        .where(LabResult.patient_id == patient_id, LabResult.kind == kind)
        .order_by(LabResult.sample_date.desc())
        .limit(3)
    )
    # Reverse so rows are oldest → newest for consecutive-pair comparison.
    rows = list(reversed(result.scalars().all()))

    if len(rows) < 2:
        return "stable"

    _ordinal: dict[Status, int] = {"green": 0, "amber": 1, "red": 2}

    statuses = [evaluate(row.value, kind) for row in rows]
    ordinals = [_ordinal[s] for s in statuses]

    # Check consecutive pairs
    all_worsening = all(ordinals[i + 1] > ordinals[i] for i in range(len(ordinals) - 1))
    all_improving = all(ordinals[i + 1] < ordinals[i] for i in range(len(ordinals) - 1))

    if all_worsening:
        return "worsening"
    if all_improving:
        return "improving"
    return "stable"
