import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, JSON, String, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base

# JSONB on PostgreSQL, plain JSON on other dialects (e.g. SQLite in tests).
JsonbType = JSON().with_variant(JSONB(), "postgresql")


class Recipe(Base):
    __tablename__ = "recipes"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    # Immutable AI-generated artifact stored as JSONB
    content: Mapped[dict] = mapped_column(JsonbType, nullable=False)
    # Derived status strings only — no numeric PHI
    clinical_context_summary: Mapped[dict | None] = mapped_column(JsonbType, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    patient: Mapped["Patient"] = relationship(back_populates="recipes")  # noqa: F821
