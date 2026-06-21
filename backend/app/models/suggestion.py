import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, JSON, SmallInteger, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base
from app.core.crypto import EncryptedString

# JSONB on PostgreSQL, plain JSON on other dialects (e.g. SQLite in tests).
JsonbType = JSON().with_variant(JSONB(), "postgresql")


class Suggestion(Base):
    __tablename__ = "suggestions"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # PHI column — EncryptedString placeholder (Phase 5 replaces with Fernet TypeDecorator)
    source_ingredient: Mapped[str] = mapped_column(EncryptedString, nullable=False)
    # Derived status strings only (e.g. {"hba1c": "red"}) — no raw numeric PHI
    clinical_context_summary: Mapped[dict | None] = mapped_column(JsonbType, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    patient: Mapped["Patient"] = relationship(back_populates="suggestions")  # noqa: F821
    alternatives: Mapped[list["SuggestionAlternative"]] = relationship(
        back_populates="suggestion", cascade="all, delete-orphan"
    )


class SuggestionAlternative(Base):
    __tablename__ = "suggestion_alternatives"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    suggestion_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("suggestions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # PHI columns — EncryptedString placeholder
    ingredient: Mapped[str] = mapped_column(EncryptedString, nullable=False)
    rationale: Mapped[str | None] = mapped_column(EncryptedString, nullable=True)
    rank: Mapped[int] = mapped_column(SmallInteger, nullable=False)

    __table_args__ = (
        CheckConstraint("rank BETWEEN 1 AND 4", name="ck_suggestion_alternatives_rank"),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    suggestion: Mapped["Suggestion"] = relationship(back_populates="alternatives")
