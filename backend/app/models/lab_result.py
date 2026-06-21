import uuid
from datetime import date, datetime

from sqlalchemy import Date, Enum, ForeignKey, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base
from app.models.enums import LabKind, LabUnit

# EncryptedString placeholder — replaced by real Fernet TypeDecorator in Phase 5.
EncryptedString = Text


class LabResult(Base):
    __tablename__ = "lab_results"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    kind: Mapped[LabKind] = mapped_column(Enum(LabKind, name="lab_kind"), nullable=False)
    # PHI column — EncryptedString placeholder
    value: Mapped[str] = mapped_column(EncryptedString, nullable=False)
    unit: Mapped[LabUnit] = mapped_column(Enum(LabUnit, name="lab_unit"), nullable=False)
    sample_date: Mapped[date] = mapped_column(Date, nullable=False)

    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())

    patient: Mapped["Patient"] = relationship(back_populates="lab_results")  # noqa: F821
