from fastapi import FastAPI, Depends

from app.api.routes.onboarding import router as onboarding_router
from app.core.config import settings
from app.core.security import get_current_patient
from app.models.patient import Patient

app = FastAPI(title=settings.app_name, debug=settings.debug)

app.include_router(onboarding_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/me")
async def get_me(patient: Patient = Depends(get_current_patient)) -> dict[str, str]:
    """
    Protected endpoint that returns the current patient's ID.
    
    This endpoint requires a valid Cognito JWT token.
    """
    return {"patient_id": str(patient.id)}
