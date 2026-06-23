"""Repository helpers for the RejectedIngredient model."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rejected_ingredient import RejectedIngredient


def _normalize(ingredient: str) -> str:
    """Strip whitespace and lower-case an ingredient name."""
    return ingredient.strip().lower()


class RejectedIngredientRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def reject(self, patient_id: uuid.UUID, ingredient: str) -> None:
        """
        Persist a rejection, ignoring duplicates.

        Normalisation: strip whitespace + lower-case before persisting so that
        "salmón" and "Salmón " resolve to the same row.

        Because EncryptedString uses non-deterministic Fernet encryption, a
        DB-level unique constraint cannot deduplicate ciphertexts. We therefore
        perform an application-level existence check before inserting.
        """
        if await self.is_rejected(patient_id, ingredient):
            return

        normalized = _normalize(ingredient)
        self._session.add(
            RejectedIngredient(
                patient_id=patient_id,
                ingredient_normalized=normalized,
                ingredient_display=ingredient.strip(),
            )
        )

    async def is_rejected(self, patient_id: uuid.UUID, ingredient: str) -> bool:
        """Return True if the normalised ingredient is in the patient's rejection list."""
        normalized = _normalize(ingredient)
        # Load all rejections for the patient and compare in Python after
        # decryption, because the ciphertexts are non-deterministic and cannot
        # be compared at the SQL level.
        result = await self._session.execute(
            select(RejectedIngredient).where(
                RejectedIngredient.patient_id == patient_id
            )
        )
        rows = result.scalars().all()
        return any(row.ingredient_normalized == normalized for row in rows)
