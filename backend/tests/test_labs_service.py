"""
Phase 12 — Traffic-light evaluation.

AC1: Table-test covers green/amber/red for each lab type.
AC2: 3 worsening HbA1c entries → trend = "worsening".
"""

import uuid
from datetime import date, timedelta

import pytest
from sqlalchemy import select

from app.models.enums import LabKind, LabUnit
from app.models.lab_result import LabResult
from app.models.patient import Patient


# ── AC1 — evaluate() table-test ───────────────────────────────────────────────


class TestEvaluate:
    """
    Table-test for app.services.labs.evaluate(value, kind) -> Status.

    Thresholds (ADA guidelines):
      HbA1c (%):             green <7, amber 7–<9, red ≥9
      Fasting glucose (mg/dL): green 70–<100, amber 100–<126, red <70 or ≥126
      Total cholesterol (mg/dL): green <200, amber 200–<240, red ≥240
      Triglycerides (mg/dL):  green <150, amber 150–<200, red ≥200
    """

    @pytest.mark.parametrize("value,kind,expected", [
        # ── HbA1c ──────────────────────────────────────────────────────────────
        ("5.5",  LabKind.hba1c, "green"),   # well-controlled
        ("6.9",  LabKind.hba1c, "green"),   # just below threshold
        ("7.0",  LabKind.hba1c, "amber"),   # at threshold
        ("8.5",  LabKind.hba1c, "amber"),   # poor control
        ("9.0",  LabKind.hba1c, "red"),     # at red threshold
        ("11.0", LabKind.hba1c, "red"),     # very poor control

        # ── Fasting glucose ────────────────────────────────────────────────────
        ("80",   LabKind.fasting_glucose, "green"),  # normal
        ("99",   LabKind.fasting_glucose, "green"),  # top of normal
        ("65",   LabKind.fasting_glucose, "red"),    # hypoglycaemia
        ("100",  LabKind.fasting_glucose, "amber"),  # pre-diabetes
        ("125",  LabKind.fasting_glucose, "amber"),  # top of pre-diabetes
        ("126",  LabKind.fasting_glucose, "red"),    # diabetes threshold
        ("200",  LabKind.fasting_glucose, "red"),    # clearly high

        # ── Total cholesterol ──────────────────────────────────────────────────
        ("150",  LabKind.total_cholesterol, "green"),
        ("199",  LabKind.total_cholesterol, "green"),
        ("200",  LabKind.total_cholesterol, "amber"),
        ("239",  LabKind.total_cholesterol, "amber"),
        ("240",  LabKind.total_cholesterol, "red"),
        ("300",  LabKind.total_cholesterol, "red"),

        # ── Triglycerides ──────────────────────────────────────────────────────
        ("100",  LabKind.triglycerides, "green"),
        ("149",  LabKind.triglycerides, "green"),
        ("150",  LabKind.triglycerides, "amber"),
        ("199",  LabKind.triglycerides, "amber"),
        ("200",  LabKind.triglycerides, "red"),
        ("500",  LabKind.triglycerides, "red"),
    ])
    def test_evaluate_returns_correct_status(self, value, kind, expected):
        from app.services.labs import evaluate

        result = evaluate(value, kind)
        assert result == expected, (
            f"evaluate({value!r}, {kind}) expected {expected!r}, got {result!r}"
        )


# ── AC2 — 3 worsening HbA1c entries → trend = "worsening" ───────────────────


class TestTrend:

    async def test_three_worsening_hba1c_entries_returns_worsening(self, db_session):
        """
        AC2: 3 HbA1c values in ascending order (worsening) → trend = "worsening".
        """
        from app.services.labs import compute_trend

        patient = Patient(cognito_sub=f"test-sub-trend-{uuid.uuid4()}")
        db_session.add(patient)
        await db_session.flush()

        today = date.today()
        # Oldest → newest: 6.9 (green), 8.5 (amber), 10.0 (red) — each worse
        for i, val in enumerate(["6.9", "8.5", "10.0"]):
            db_session.add(LabResult(
                patient_id=patient.id,
                kind=LabKind.hba1c,
                value=val,
                unit=LabUnit.percent,
                sample_date=today - timedelta(days=(2 - i) * 30),
            ))
        await db_session.commit()

        trend = await compute_trend(patient.id, LabKind.hba1c, db_session)
        assert trend == "worsening", f"Expected 'worsening', got {trend!r}"

    async def test_three_improving_hba1c_entries_returns_improving(self, db_session):
        """3 HbA1c values in descending order → trend = "improving"."""
        from app.services.labs import compute_trend

        patient = Patient(cognito_sub=f"test-sub-trend-{uuid.uuid4()}")
        db_session.add(patient)
        await db_session.flush()

        today = date.today()
        # Oldest → newest: 10.0 (red), 8.5 (amber), 6.9 (green) — improving
        for i, val in enumerate(["10.0", "8.5", "6.9"]):
            db_session.add(LabResult(
                patient_id=patient.id,
                kind=LabKind.hba1c,
                value=val,
                unit=LabUnit.percent,
                sample_date=today - timedelta(days=(2 - i) * 30),
            ))
        await db_session.commit()

        trend = await compute_trend(patient.id, LabKind.hba1c, db_session)
        assert trend == "improving", f"Expected 'improving', got {trend!r}"

    async def test_stable_hba1c_entries_returns_stable(self, db_session):
        """3 identical HbA1c values → trend = "stable"."""
        from app.services.labs import compute_trend

        patient = Patient(cognito_sub=f"test-sub-trend-{uuid.uuid4()}")
        db_session.add(patient)
        await db_session.flush()

        today = date.today()
        for i in range(3):
            db_session.add(LabResult(
                patient_id=patient.id,
                kind=LabKind.hba1c,
                value="7.5",
                unit=LabUnit.percent,
                sample_date=today - timedelta(days=(2 - i) * 30),
            ))
        await db_session.commit()

        trend = await compute_trend(patient.id, LabKind.hba1c, db_session)
        assert trend == "stable", f"Expected 'stable', got {trend!r}"

    async def test_fewer_than_two_entries_returns_stable(self, db_session):
        """With only one entry, trend cannot be computed → stable."""
        from app.services.labs import compute_trend

        patient = Patient(cognito_sub=f"test-sub-trend-{uuid.uuid4()}")
        db_session.add(patient)
        await db_session.flush()

        db_session.add(LabResult(
            patient_id=patient.id,
            kind=LabKind.hba1c,
            value="7.5",
            unit=LabUnit.percent,
            sample_date=date.today(),
        ))
        await db_session.commit()

        trend = await compute_trend(patient.id, LabKind.hba1c, db_session)
        assert trend == "stable", f"Expected 'stable', got {trend!r}"


# ── GET /labs/trends HTTP-level test ──────────────────────────────────────────


async def test_get_trends_returns_status_and_trend_fields(db_session):
    """
    GET /labs/trends returns a list of data points each with a status field
    and an overall trend per kind.
    """
    from fastapi.testclient import TestClient

    from app.core.security import get_current_patient
    from app.db.session import get_db
    from app.main import app

    patient = Patient(cognito_sub=f"test-sub-trends-{uuid.uuid4()}")
    db_session.add(patient)
    await db_session.flush()

    today = date.today()
    for i, val in enumerate(["7.0", "7.5", "8.0"]):
        db_session.add(LabResult(
            patient_id=patient.id,
            kind=LabKind.hba1c,
            value=val,
            unit=LabUnit.percent,
            sample_date=today - timedelta(days=(2 - i) * 30),
        ))
    await db_session.commit()

    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_patient] = lambda: patient
    client = TestClient(app)
    try:
        response = client.get("/labs/trends")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200, response.text
    data = response.json()

    # Expect a list of trend summaries, one per lab kind that has data
    assert isinstance(data, list), "Response must be a list"
    assert len(data) >= 1

    # Each item must have the required fields
    item = data[0]
    assert "kind" in item
    assert "entries" in item
    assert "trend" in item

    # Each entry must have a status field
    for entry in item["entries"]:
        assert "status" in entry
        assert entry["status"] in {"green", "amber", "red"}
