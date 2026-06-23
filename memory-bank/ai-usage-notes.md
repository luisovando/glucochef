# AI usage notes

Incremental log of AI-assisted prompts, decisions, and outputs for the GlucoChef project.

---

## 2026-06-21 — Phase 0 / AI4-37

- Executed `@glucochef-phase-executor Phase 0 / AI4-37`.
- Created backend package (`backend/app`, `backend/tests`, `pyproject.toml`) and root `.gitignore`.
- Scaffolded frontend with `pnpm create next-app@14 frontend --ts --app --tailwind --eslint --src-dir --import-alias "@/*"`.
- Resolved pnpm ignored-builds policy by approving `unrs-resolver` build scripts (created `frontend/pnpm-workspace.yaml` with `allowBuilds` config — this is the correct pnpm 11+ approach even for non-workspace projects).
- Verified acceptance criteria:
  - `tree -L 2 backend frontend` shows both trees.
  - `python -c "import app"` succeeds from `backend/`.
  - `pnpm --dir frontend build` succeeds.
- Created branch `feat/ai4-37-phase-0-repository-scaffolding`; commit not yet applied (user rejected tool call).

---

## 2026-06-21 — Phase 1 / AI4-38

- Executed `@glucochef-phase-executor Phase 1 / AI4-38`.
- Dependency check: Phase 0 repository scaffolding present (`backend/app`, `backend/tests`, `pyproject.toml`).
- Added `fastapi`, `uvicorn[standard]`, `pydantic-settings`, `python-dotenv` to `backend/pyproject.toml`.
- Created `backend/app/core/config.py` (Pydantic `BaseSettings` reading `.env`) and `backend/app/core/__init__.py`.
- Implemented `backend/app/main.py` with `FastAPI` app and `GET /health` returning `{"status": "ok"}`.
- Created local `.venv` and installed backend in editable mode.
- Verified acceptance criteria:
  - `uvicorn app.main:app` starts without error (server log: `Application startup complete`).
  - `curl localhost:8000/health` returns HTTP 200 with `{"status":"ok"}`.
- Proposed git artifacts: branch `feat/ai4-38-phase-1-backend-bootstrap`, commit `feat(AI4-38): phase 1 — backend bootstrap with health check`.
- Cleaned up editable-install `.egg-info` build artifact; `.venv` is ignored by root `.gitignore`.

---

## 2026-06-21 — Phase 2 / AI4-39 (database & migrations)

- Executed `@glucochef-phase-executor Phase 2 / AI4-39`.
- Added `sqlalchemy>=2.0.0`, `asyncpg>=0.29.0`, `alembic>=1.13.0` to `pyproject.toml` runtime deps.
- Added `pytest>=8.0.0`, `pytest-asyncio>=0.23.0`, `aiosqlite>=0.20.0`, `httpx>=0.27.0` as dev deps; added `[tool.pytest.ini_options]` with `asyncio_mode = "auto"`.
- Created `docker-compose.yml` with `postgres:16`, named volume, healthcheck, port bound to `127.0.0.1:5432`.
- Created `backend/app/db/base.py` (`DeclarativeBase`), `backend/app/db/session.py` (async engine + `get_db` generator).
- Initialised Alembic (`alembic init backend/alembic`); configured `env.py` for async engine with `NullPool`.
- Verified: `docker compose up -d postgres` healthy; `alembic upgrade head` exits 0.
- Commit: `feat(AI4-39): phase 2 — database & migrations`.

---

## 2026-06-21 — Phase 3 / AI4-39 (core ERD models)

- Executed `@glucochef-phase-executor Phase 3 / AI4-39`.
- Consulted `docs/erd.md` — 12 tables after 3NF normalisation (4 child tables extracted from `nutritional_profiles`, `suggestion_alternatives` split from `suggestions`).
- Created `backend/app/models/`: `enums.py`, `patient.py`, `nutritional_profile.py`, `rejected_ingredient.py`, `lab_result.py`, `suggestion.py`, `recipe.py`, `audit_log_entry.py`, `__init__.py`.
- PHI columns use `EncryptedString = Text` placeholder (per PRD Phase 3 instruction; Phase 5 replaces with Fernet `TypeDecorator`).
- `audit_log_entries.patient_id` uses `SET NULL` / no cascade — forensic rows must outlive the patient.
- Updated `alembic/env.py` to import `app.models` so all mappers register with `Base.metadata` for autogenerate.
- Created `tests/conftest.py` (SQLite in-memory, session-scoped engine) and `tests/test_patient_model.py`.
- Verified acceptance criteria:
  - `alembic upgrade head` exits 0; migration applied.
  - `psql` confirmed all 12 domain tables with correct FK constraints.
  - `pytest test_insert_patient` PASSED.
- Commit: `feat(AI4-39): phase 3 — core ERD models and init schema migration`.

---

## 2026-06-21 — Post-phase 3 code review fixes

Three separate review passes surfaced and fixed the following issues.

**Schema type corrections (commit `fix(models): correct schema types…`):**
- All timestamp columns: `DateTime()` → `DateTime(timezone=True)` → `TIMESTAMPTZ` in PostgreSQL (ERD specifies TIMESTAMPTZ throughout).
- JSON columns on `suggestions` and `recipes`: generic `JSON` → `JSON().with_variant(JSONB(), "postgresql")` — JSONB is binary, indexable, and matches the ERD spec. Dialect variant keeps SQLite tests working.
- `audit_log_entries.ip_address`: `String(45)` → `String(45).with_variant(INET(), "postgresql")` — PostgreSQL validates IP addresses at the DB layer.
- Consolidated `EncryptedString = Text` alias from 5 separate files into `backend/app/core/crypto.py`; all models now import from there. Phase 5 swap is a single-file change.
- Migration regenerated (`9fc8fec44ae1`) after dropping the old one (`1ecfa417d02a`).
- Test isolation improved: `conftest.py` now uses a connection-level SAVEPOINT with an `after_transaction_end` listener so mid-test commits don't escape to the in-memory DB.
- Removed redundant `@pytest.mark.asyncio` (asyncio_mode = "auto" covers it) and unused `import pytest`.

**Security fixes (commit `fix(security): remove hardcoded credentials…`):**
- `config.py`: removed `database_url` hardcoded default (`postgresql+asyncpg://glucochef:glucochef@...`); field is now required — missing value raises `ValidationError` at startup.
- `docker-compose.yml`: credentials moved to env vars; port binding tightened to `127.0.0.1:5432`.
- `.gitignore`: narrowed `.env*` glob to `.env` + `.env.*` with `!.env.example` negation.
- Added `.env.example` at repo root.

**Per-service env structure (commits `chore(env): per-service .env.example…` and `chore(env): fail-fast Compose vars…`):**
- Root `.env` / `.env.example` scoped to Docker Compose only (3 Postgres vars).
- `backend/.env.example` documents all backend vars across all phases (database URL, Cognito, encryption key, AI provider).
- `frontend/.env.example` documents all frontend vars (`NEXT_PUBLIC_*`), including `NEXT_PUBLIC_` prefix explanation and browser-visibility warning.
- `docker-compose.yml` Postgres vars upgraded to `${VAR:?message}` — fails fast with actionable error if `.env` is missing.
- `ENCRYPTION_KEY=change_me` replaced with `ENCRYPTION_KEY=REPLACE_WITH_GENERATED_FERNET_KEY` — `change_me` is not a valid 32-byte Fernet key.

---

## 2026-06-22 — Phase 6 / AI4-43 (onboarding API)

- Executed `@glucochef-phase-executor Phase 6 / AI4-43`.
- Dependency check: Phase 5 encryption + audit tests pass (12/12) after populating `backend/.env` `ENCRYPTION_KEY` with a valid Fernet key.
- Added `consent` value to `AuditAction` enum and created Alembic migration `e3d89e75cb1c` to add the value to PostgreSQL `audit_action` enum.
- Created `backend/app/schemas/onboarding.py` with `OnboardingRequest` (consent validator) and `OnboardingResponse`.
- Created `backend/app/api/routes/onboarding.py` with `POST /onboarding`:
  - Protected by `get_current_patient`.
  - Upserts `NutritionalProfile` per patient.
  - Replaces related PHI rows (`medications`, `allergies`, `intolerances`) and non-PHI rows (`dietary_preferences`).
  - Replaces `rejected_ingredients` rows.
  - Records explicit consent on the `Patient` record.
  - Writes two audit entries (`write onboarding`, `consent`) in the same transaction.
- Registered `onboarding_router` in `backend/app/main.py`.
- Added `backend/tests/test_onboarding.py` with three AC tests:
  - `test_authenticated_post_creates_profile` — 201 + profile id.
  - `test_unauthenticated_post_returns_401` — no auth header returns 401.
  - `test_posting_twice_updates_profile` — second POST updates existing profile, no duplicate.
- Verified full backend suite: 15 passed, 0 failed.
- Proposed git artifacts: branch `feat/ai4-43-phase-6-onboarding-api`, commit `feat(AI4-43): phase 6 — onboarding API`.
