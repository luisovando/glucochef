import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base
from app.core.crypto import EncryptedString


class RejectedIngredient(Base):
    __tablename__ = "rejected_ingredients"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # PHI columns — EncryptedString placeholder (Phase 5 replaces with Fernet TypeDecorator)
    ingredient_normalized: Mapped[str] = mapped_column(EncryptedString, nullable=False)
    ingredient_display: Mapped[str] = mapped_column(EncryptedString, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    patient: Mapped["Patient"] = relationship(back_populates="rejected_ingredients")  # noqa: F821
