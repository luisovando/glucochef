"""Ingredient management routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_patient
from app.db.session import get_db
from app.models.patient import Patient
from app.repositories.rejected_ingredient import RejectedIngredientRepository

router = APIRouter(prefix="/ingredients", tags=["ingredients"])


@router.post("/{name}/reject")
async def reject_ingredient(
    name: str,
    patient: Patient = Depends(get_current_patient),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """
    Persist a rejected ingredient for the authenticated patient.

    The ingredient name is normalised (stripped + lower-cased) before
    persistence so that duplicate submissions with different casing or
    surrounding whitespace result in a single row.
    """
    if not name.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Ingredient name must not be blank.",
        )
    repo = RejectedIngredientRepository(db)
    await repo.reject(patient.id, name)
    await db.commit()
    return {"status": "rejected", "ingredient": name.strip()}
