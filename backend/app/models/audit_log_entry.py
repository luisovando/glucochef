import uuid
from datetime import datetime

from sqlalchemy import Enum, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base
from app.models.enums import AuditAction, AuditResource


class AuditLogEntry(Base):
    __tablename__ = "audit_log_entries"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # Nullable FK — no CASCADE; audit rows are forensic and must outlive the patient.
    patient_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
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
    resource_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    event_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now(), index=True)

    patient: Mapped["Patient"] = relationship(back_populates="audit_log_entries")  # noqa: F821
