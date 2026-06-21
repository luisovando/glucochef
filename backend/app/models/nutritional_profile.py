import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base

# EncryptedString placeholder — replaced by the real Fernet TypeDecorator in Phase 5.
EncryptedString = Text


class NutritionalProfile(Base):
    __tablename__ = "nutritional_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    # PHI columns — EncryptedString placeholder
    diabetes_type: Mapped[str | None] = mapped_column(EncryptedString, nullable=True)
    diagnosis_date: Mapped[str | None] = mapped_column(EncryptedString, nullable=True)
    additional_notes: Mapped[str | None] = mapped_column(EncryptedString, nullable=True)

    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now(), onupdate=func.now()
    )

    patient: Mapped["Patient"] = relationship(back_populates="nutritional_profile")  # noqa: F821
    medications: Mapped[list["Medication"]] = relationship(
        back_populates="nutritional_profile", cascade="all, delete-orphan"
    )
    allergies: Mapped[list["Allergy"]] = relationship(
        back_populates="nutritional_profile", cascade="all, delete-orphan"
    )
    intolerances: Mapped[list["Intolerance"]] = relationship(
        back_populates="nutritional_profile", cascade="all, delete-orphan"
    )
    dietary_preferences: Mapped[list["DietaryPreference"]] = relationship(
        back_populates="nutritional_profile", cascade="all, delete-orphan"
    )


class Medication(Base):
    __tablename__ = "medications"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    nutritional_profile_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("nutritional_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # PHI columns — EncryptedString placeholder
    name: Mapped[str] = mapped_column(EncryptedString, nullable=False)
    dosage: Mapped[str | None] = mapped_column(EncryptedString, nullable=True)

    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())

    nutritional_profile: Mapped["NutritionalProfile"] = relationship(back_populates="medications")


class Allergy(Base):
    __tablename__ = "allergies"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    nutritional_profile_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("nutritional_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # PHI columns — EncryptedString placeholder
    substance: Mapped[str] = mapped_column(EncryptedString, nullable=False)
    severity: Mapped[str | None] = mapped_column(EncryptedString, nullable=True)

    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())

    nutritional_profile: Mapped["NutritionalProfile"] = relationship(back_populates="allergies")


class Intolerance(Base):
    __tablename__ = "intolerances"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    nutritional_profile_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("nutritional_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # PHI column — EncryptedString placeholder
    substance: Mapped[str] = mapped_column(EncryptedString, nullable=False)

    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())

    nutritional_profile: Mapped["NutritionalProfile"] = relationship(back_populates="intolerances")


class DietaryPreference(Base):
    __tablename__ = "dietary_preferences"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    nutritional_profile_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("nutritional_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Not PHI — cultural/dietary tag
    preference: Mapped[str] = mapped_column(String(256), nullable=False)

    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())

    nutritional_profile: Mapped["NutritionalProfile"] = relationship(
        back_populates="dietary_preferences"
    )
