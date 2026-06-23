"""Phase 11 — Lab registration endpoint.

POST /labs accepts a single lab result (HbA1c, fasting glucose, total
cholesterol, or triglycerides), validates the value range, persists the row
(value encrypted at rest), and writes an audit entry.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import audit
from app.core.security import get_current_patient
from app.db.session import get_db
from app.models.enums import AuditAction, AuditResource
from app.models.lab_result import LabResult
from app.models.patient import Patient
from app.schemas.labs import LabCreateRequest, LabCreateResponse

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
