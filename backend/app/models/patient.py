import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    cognito_sub: Mapped[str] = mapped_column(String(256), nullable=False, unique=True, index=True)
    display_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    sex_at_birth: Mapped[str | None] = mapped_column(String(64), nullable=True)
    consent_accepted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    consent_accepted_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # relationships
    nutritional_profile: Mapped["NutritionalProfile"] = relationship(  # noqa: F821
        back_populates="patient", uselist=False, cascade="all, delete-orphan"
    )
    rejected_ingredients: Mapped[list["RejectedIngredient"]] = relationship(  # noqa: F821
        back_populates="patient", cascade="all, delete-orphan"
    )
    lab_results: Mapped[list["LabResult"]] = relationship(  # noqa: F821
        back_populates="patient", cascade="all, delete-orphan"
    )
    suggestions: Mapped[list["Suggestion"]] = relationship(  # noqa: F821
        back_populates="patient", cascade="all, delete-orphan"
    )
    recipes: Mapped[list["Recipe"]] = relationship(  # noqa: F821
        back_populates="patient", cascade="all, delete-orphan"
    )
    audit_log_entries: Mapped[list["AuditLogEntry"]] = relationship(  # noqa: F821
        back_populates="patient"
        # no cascade — audit rows are forensic and must outlive the patient
    )
