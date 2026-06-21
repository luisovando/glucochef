import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, JSON, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base


class Recipe(Base):
    __tablename__ = "recipes"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    # Immutable AI-generated artifact stored as JSONB
    content: Mapped[dict] = mapped_column(JSON, nullable=False)
    # Derived status strings only — no numeric PHI
    clinical_context_summary: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())

    patient: Mapped["Patient"] = relationship(back_populates="recipes")  # noqa: F821
