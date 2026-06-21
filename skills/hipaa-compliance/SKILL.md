---
name: hipaa-compliance
description: >
  PHI handling conventions for GlucoChef. Read this skill before implementing
  any phase that touches PHI columns, authentication, or audit logging.
  Applies to: Phase 3 (models), Phase 4 (JWT auth), Phase 5 (encryption + audit),
  Phase 6 (onboarding), Phase 11 (lab registration), Phase 12 (lab trends).
---

# HIPAA-Aligned Practices — GlucoChef

GlucoChef targets HIPAA-aligned practices without formal certification.
This skill encodes what that means at the code level for each PHI-touching concern.

---

## 1. PHI scope — what counts as PHI in this project

PHI (Protected Health Information) includes any data that could identify a patient
and relates to their health condition, treatment, or payment.

| Column / field | PHI? | Notes |
|---|---|---|
| `lab_results.hba1c` | ✅ Yes | Clinical value tied to patient |
| `lab_results.fasting_glucose` | ✅ Yes | Clinical value |
| `lab_results.cholesterol` | ✅ Yes | Clinical value |
| `lab_results.triglycerides` | ✅ Yes | Clinical value |
| `nutritional_profiles.medications` | ✅ Yes | Medical treatment data |
| `nutritional_profiles.allergies` | ✅ Yes | Health condition data |
| `nutritional_profiles.intolerances` | ✅ Yes | Health condition data |
| `rejected_ingredients.ingredient` | ✅ Yes | Can imply health conditions |
| `patients.email` | ⚠️ PHI-adjacent | Managed by Cognito; not stored in RDS |
| `audit_log_entries.*` | ⚠️ Contains PHI refs | Store actor + action + resource, never raw values |
| `recipes.*` | ❌ No | Generated content, not clinical data |
| `suggestions.*` | ❌ No | Generated content, not clinical data |

**Rule:** When in doubt, classify as PHI and apply encryption.

---

## 2. Encryption at rest — EncryptedString

All PHI columns must use `EncryptedString`, the SQLAlchemy `TypeDecorator`
defined in `app/core/crypto.py`.

**Implementation pattern (Phase 5):**
```python
from app.core.crypto import EncryptedString

class LabResult(Base):
    hba1c: Mapped[str] = mapped_column(EncryptedString)
    fasting_glucose: Mapped[str] = mapped_column(EncryptedString)
    cholesterol: Mapped[str] = mapped_column(EncryptedString)
    triglycerides: Mapped[str] = mapped_column(EncryptedString)
```

**Verification test (required for Phase 5 AC):**
```python
async def test_phi_is_encrypted_at_rest(session):
    # Write through ORM
    lab = LabResult(patient_id=..., hba1c="7.2", ...)
    session.add(lab)
    await session.commit()

    # Read raw bytes directly — bypass ORM
    raw = await session.execute(text("SELECT hba1c FROM lab_results LIMIT 1"))
    assert raw.scalar() != "7.2"  # must be ciphertext
```

**Anti-patterns:**
- Never use `String` or `Text` for PHI columns — use `EncryptedString`
- Never log raw PHI values — log resource IDs only
- Never store PHI in Redis, cache layers, or session storage

**Key management:**
- `ENCRYPTION_KEY` is a Fernet key loaded from environment via `config.py`
- Never hardcode the key; never commit it to the repo
- Rotation procedure is deferred to v2

---

## 3. Encryption in transit — TLS

All connections to RDS and all API endpoints must use TLS 1.2+.

- FastAPI → RDS: enforced via `asyncpg` SSL mode in `app/db/session.py`
- Client → FastAPI: enforced at the load balancer / App Runner layer (Phase 25)
- Development: local Docker postgres does not require TLS; flag this in `.env.example`

---

## 4. Authentication — Cognito JWT (Phase 4)

Every PHI endpoint must be protected by the `get_current_patient` FastAPI dependency.

```python
from app.core.security import get_current_patient

@router.post("/labs", status_code=201)
async def create_lab(
    payload: LabCreateRequest,
    patient: Patient = Depends(get_current_patient),  # required
    ...
):
```

**What `get_current_patient` must do:**
1. Extract `Authorization: Bearer {token}` from the request header
2. Fetch the Cognito JWKS from `https://cognito-idp.{region}.amazonaws.com/{pool_id}/.well-known/jwks.json`
3. Verify the token signature, expiry, and `aud` claim
4. Resolve and return the `Patient` row for the `sub` claim
5. Raise HTTP 401 for any failure (invalid signature, expired, patient not found)

**Anti-patterns:**
- Never trust a patient ID from the request body — always resolve from the verified JWT
- Never return PHI in a 401 or 403 response body
- Never disable auth for "convenience" in dev — use a test fixture that mocks JWKS

---

## 5. Audit logging (Phase 5)

Every PHI read or write must produce exactly one `AuditLogEntry` row.

**Schema:**
```
audit_log_entries
  id          UUID  PK
  actor_id    UUID  FK → patients.id
  action      TEXT  e.g. "read labs", "write lab", "denied read labs"
  resource    TEXT  e.g. "lab_result:{id}"
  timestamp   TIMESTAMPTZ
```

**Usage pattern (via context manager):**
```python
from app.core.audit import audit

@router.get("/labs/trends")
async def get_trends(patient: Patient = Depends(get_current_patient), ...):
    async with audit(actor=patient, action="read labs", resource="lab_results"):
        results = await lab_service.get_trends(patient.id)
    return results
```

**Required audit actions:**
| Endpoint | Action string |
|---|---|
| `POST /onboarding` | `"write onboarding"` |
| `POST /labs` | `"write lab"` |
| `GET /labs/trends` | `"read labs"` |
| `GET /labs/trends` (other patient) | `"denied read labs"` |
| `POST /onboarding` (consent) | `"consent recorded"` |

**Verification test (required for Phase 5 AC):**
```python
async def test_phi_read_creates_audit_entry(client, patient_token):
    await client.get("/labs/trends", headers={"Authorization": f"Bearer {patient_token}"})
    entries = await AuditLogEntry.query.filter_by(action="read labs").all()
    assert len(entries) == 1
    assert entries[0].actor_id == patient.id
```

**Anti-patterns:**
- Never store raw PHI values in `resource` — store resource type + ID only
- Never skip the audit dependency on a PHI endpoint, even in tests
- The audit write must happen inside the same transaction as the PHI operation

---

## 6. Explicit consent (Phase 6)

Before creating a `NutritionalProfile`, the patient must explicitly consent to
PHI storage. This is enforced at the API level, not left to the frontend.

```python
class OnboardingRequest(BaseModel):
    diabetes_type: DiabetesType
    medications: list[str]
    allergies: list[str]
    ...
    consent: bool  # must be True — validated by Pydantic

    @field_validator("consent")
    def consent_must_be_true(cls, v):
        if not v:
            raise ValueError("Explicit consent is required to store health data")
        return v
```

On successful onboarding, write an audit entry with `action="consent recorded"`.

---

## 7. PHI and the AI provider (Phases 8, 9, 10, 13)

PHI must never be sent verbatim to the AI provider (OpenAI or Claude API).

**What CAN be sent:**
- Structural metadata: `diabetes_type`, `carb_limit_level` (green/amber/red), `allergy_categories`
- Normalised counts: `num_rejected_ingredients`, `has_active_labs`

**What must NOT be sent:**
- Raw lab values (e.g., `hba1c=7.2`)
- Medication names
- Allergy text as entered by the patient

**Redaction is enforced inside `app/ai/provider.py`.** Route handlers pass
the full `NutritionalProfile` and `LabResult` objects; the provider translates
them to a redacted prompt dict before making the API call.

Every prompt sent to the AI provider must be logged (redacted form) to
`memory-bank/ai-usage-notes.md` per the AI usage log requirement.

---

## 8. Right to erasure

Patients can request deletion of all their PHI. This mechanism must be
explicitly designed — it is not automatic.

**Scope of erasure:**
- `lab_results` rows for the patient
- `nutritional_profiles` row
- `rejected_ingredients` rows
- `suggestions` and `recipes` rows (generated content linked to patient)

**Audit log entries are NOT deleted** — they are evidence of access, not PHI.

Implementation is deferred to v2 but the data model must not make it
structurally impossible (i.e., all PHI tables must have a `patient_id` FK
that allows a single cascading delete or a targeted purge query).

---

## 9. Implementation correctness checks

These are code-level verifications, separate from formal HIPAA compliance.
Run these checks as part of Phase 22 (test hardening).

```python
# 1. No PHI column is plain String/Text
def test_no_unencrypted_phi_columns():
    for model in [LabResult, NutritionalProfile, RejectedIngredient]:
        for col in model.__table__.columns:
            if col.name in PHI_COLUMNS:
                assert isinstance(col.type, EncryptedString), \
                    f"{model.__name__}.{col.name} must be EncryptedString"

# 2. No PHI endpoint skips auth
def test_all_phi_routes_require_auth(client):
    phi_routes = ["/labs", "/labs/trends", "/onboarding"]
    for route in phi_routes:
        response = client.get(route)  # no auth header
        assert response.status_code == 401

# 3. Every PHI read produces an audit entry
# (covered by Phase 5 AC tests)
```
