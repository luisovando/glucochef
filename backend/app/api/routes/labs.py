"""Lab endpoints.

Phase 11 — POST /labs: register a lab result (encrypted, audited).
Phase 12 — GET /labs/trends: return history with traffic-light status per
            data point and an overall trend per lab kind.
"""

from datetime import date

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import audit
from app.core.security import get_current_patient
from app.db.session import get_db
from app.models.enums import AuditAction, AuditResource, LabKind
from app.models.lab_result import LabResult
from app.models.patient import Patient
from app.schemas.labs import LabCreateRequest, LabCreateResponse
from app.services.labs import Status, Trend, compute_trend, evaluate

router = APIRouter(prefix="/labs", tags=["labs"])


@router.post("", response_model=LabCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_lab(
    payload: LabCreateRequest,
    patient: Patient = Depends(get_current_patient),
    db: AsyncSession = Depends(get_db),
) -> LabCreateResponse:
    """
    Register a new lab result for the authenticated patient.

    - Value is validated against clinical ranges before persistence.
    - The value column uses EncryptedString (Fernet AES-256) at rest.
    - One AuditLogEntry is written inside the same transaction.
    """
    try:
        lab = LabResult(
            patient_id=patient.id,
            kind=payload.kind,
            value=payload.value,
            unit=payload.unit,
            sample_date=payload.sample_date,
        )
        db.add(lab)
        await db.flush()

        async with audit(
            session=db,
            actor=patient,
            action=AuditAction.write,
            resource=AuditResource.labs,
            resource_id=lab.id,
        ):
            pass

        await db.commit()
    except Exception:
        await db.rollback()
        raise

    return LabCreateResponse(lab_id=str(lab.id))


# ── Phase 12 — GET /labs/trends ───────────────────────────────────────────────


class LabEntryResponse(BaseModel):
    lab_id: str
    value: str
    unit: str
    sample_date: date
    status: Status


class LabTrendResponse(BaseModel):
    kind: str
    entries: list[LabEntryResponse]
    trend: Trend


@router.get("/trends", response_model=list[LabTrendResponse])
async def get_lab_trends(
    patient: Patient = Depends(get_current_patient),
    db: AsyncSession = Depends(get_db),
) -> list[LabTrendResponse]:
    """
    Return lab history with traffic-light status per entry and an overall
    trend per lab kind.

    Only lab kinds that have at least one result for the patient are included.
    Audit entry written for PHI read.
    """
    result = await db.execute(
        select(LabResult)
        .where(LabResult.patient_id == patient.id)
        .order_by(LabResult.kind.asc(), LabResult.sample_date.asc())
    )
    all_labs = result.scalars().all()

    # Group by kind
    by_kind: dict[LabKind, list[LabResult]] = {}
    for lab in all_labs:
        by_kind.setdefault(lab.kind, []).append(lab)

    trends: list[LabTrendResponse] = []
    for kind, labs in by_kind.items():
        entries = [
            LabEntryResponse(
                lab_id=str(lab.id),
                value=lab.value,
                unit=lab.unit.value,
                sample_date=lab.sample_date,
                status=evaluate(lab.value, kind),
            )
            for lab in labs
        ]
        trend = await compute_trend(patient.id, kind, db)
        trends.append(LabTrendResponse(kind=kind.value, entries=entries, trend=trend))

    async with audit(
        session=db,
        actor=patient,
        action=AuditAction.read,
        resource=AuditResource.labs,
    ):
        pass

    await db.commit()
    return trends
