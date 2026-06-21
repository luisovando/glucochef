import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base

# EncryptedString placeholder — replaced by real Fernet TypeDecorator in Phase 5.
EncryptedString = Text


class RejectedIngredient(Base):
    __tablename__ = "rejected_ingredients"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # PHI columns — EncryptedString placeholder
    ingredient_normalized: Mapped[str] = mapped_column(EncryptedString, nullable=False)
    ingredient_display: Mapped[str] = mapped_column(EncryptedString, nullable=False)

    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())

    patient: Mapped["Patient"] = relationship(back_populates="rejected_ingredients")  # noqa: F821
