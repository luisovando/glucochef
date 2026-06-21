import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base
from app.core.crypto import EncryptedString
from app.models.enums import LabKind, LabUnit


class LabResult(Base):
    __tablename__ = "lab_results"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    kind: Mapped[LabKind] = mapped_column(Enum(LabKind, name="lab_kind"), nullable=False)
    # PHI column — EncryptedString placeholder (Phase 5 replaces with Fernet TypeDecorator)
    value: Mapped[str] = mapped_column(EncryptedString, nullable=False)
    unit: Mapped[LabUnit] = mapped_column(Enum(LabUnit, name="lab_unit"), nullable=False)
    sample_date: Mapped[date] = mapped_column(Date, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    patient: Mapped["Patient"] = relationship(back_populates="lab_results")  # noqa: F821
