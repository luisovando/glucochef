import enum


class LabKind(str, enum.Enum):
    hba1c = "hba1c"
    fasting_glucose = "fasting_glucose"
    total_cholesterol = "total_cholesterol"
    triglycerides = "triglycerides"


class LabUnit(str, enum.Enum):
    percent = "percent"
    mg_per_dl = "mg_per_dl"


class AuditAction(str, enum.Enum):
    read = "read"
    write = "write"
    delete = "delete"
    consent = "consent"


class AuditResource(str, enum.Enum):
    onboarding = "onboarding"
    labs = "labs"
    suggestions = "suggestions"
    recipes = "recipes"
    rejections = "rejections"
