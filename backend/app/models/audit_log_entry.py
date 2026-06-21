import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Uuid
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base
from app.models.enums import AuditAction, AuditResource

# INET on PostgreSQL (IP address validation + binary storage), VARCHAR(45) elsewhere.
InetType = String(45).with_variant(INET(), "postgresql")


class AuditLogEntry(Base):
    __tablename__ = "audit_log_entries"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    # Nullable FK — no CASCADE; audit rows are forensic and must outlive the patient.
    patient_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("patients.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    actor_cognito_sub: Mapped[str] = mapped_column(String(256), nullable=False)
    action: Mapped[AuditAction] = mapped_column(
        Enum(AuditAction, name="audit_action"), nullable=False
    )
    resource: Mapped[AuditResource] = mapped_column(
        Enum(AuditResource, name="audit_resource"), nullable=False
    )
    resource_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(InetType, nullable=True)
    event_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )

    patient: Mapped["Patient"] = relationship(back_populates="audit_log_entries")  # noqa: F821
