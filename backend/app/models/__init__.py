# Import all models here so SQLAlchemy's mapper and Base.metadata know about every table.
# Alembic's env.py imports Base, which then sees all registered mappers.

from app.models.patient import Patient  # noqa: F401
from app.models.nutritional_profile import (  # noqa: F401
    Allergy,
    DietaryPreference,
    Intolerance,
    Medication,
    NutritionalProfile,
)
from app.models.rejected_ingredient import RejectedIngredient  # noqa: F401
from app.models.lab_result import LabResult  # noqa: F401
from app.models.suggestion import Suggestion, SuggestionAlternative  # noqa: F401
from app.models.recipe import Recipe  # noqa: F401
from app.models.audit_log_entry import AuditLogEntry  # noqa: F401

__all__ = [
    "Patient",
    "NutritionalProfile",
    "Medication",
    "Allergy",
    "Intolerance",
    "DietaryPreference",
    "RejectedIngredient",
    "LabResult",
    "Suggestion",
    "SuggestionAlternative",
    "Recipe",
    "AuditLogEntry",
]
