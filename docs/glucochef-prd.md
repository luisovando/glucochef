# GlucoChef — Agent-Optimised PRD

**Audience:** AI coding agents (Cursor, Claude Code, Windsurf Cascade) and human reviewers verifying agent output.
**Source of truth:** `/docs/product-doc.md` (product scope) and `skills/glucochef-conventions/SKILL.md` (stack, MVP boundaries, anti-patterns).
**Format rules:** every phase is atomic, sequential, and completable by an agent in **5–15 minutes**. Each phase declares dependencies, verifiable acceptance criteria, and an explicit "Do not change" list.

---

## How to use this PRD

1. Work phases **in order**. Do not start phase N until phase N-1's acceptance criteria pass.
2. Treat acceptance criteria as a **machine-checkable contract**. If a criterion cannot be verified with a command, log a comment in the PR explaining why and propose a check.
3. Respect the **Do not change** block of every phase. Out-of-scope refactors are rejected even if "cleaner".
4. If a phase blocks (missing decision, ambiguity, or broken upstream), stop and open an issue rather than improvising.
5. Read `Non-goals` (§ end of document) before proposing any feature not listed below.

---

## Stack invariants (do not deviate)

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python 3.11+) |
| Frontend | Next.js 14 (App Router) as PWA |
| Database | PostgreSQL (local Docker for dev, AWS RDS for deploy) |
| ORM / Migrations | SQLAlchemy 2.x + Alembic |
| Auth | AWS Cognito (JWT verification on backend) |
| AI | OpenAI or Anthropic Claude API (single provider chosen in Phase 9) |
| Tests | Pytest (backend), Playwright (frontend E2E) |
| CI/CD | GitHub Actions → AWS Free Tier |

Any deviation requires an entry in `memory-bank/decisions.md` before the phase that deviates is started.

---

## Phase 0 — Repository scaffolding

**Goal:** create the top-level folders for backend and frontend with empty but importable packages.

**Dependencies:** none.

**Steps:**
- Create `backend/` with `pyproject.toml`, `app/__init__.py`, `app/main.py`, `tests/__init__.py`.
- Create `frontend/` via `pnpm create next-app@14 frontend --ts --app --tailwind --eslint --src-dir --import-alias "@/*"`.
- Add `.gitignore` entries for `.venv`, `__pycache__`, `node_modules`, `.next`, `.env*`.

**Acceptance criteria:**
- `tree -L 2 backend frontend` shows both trees.
- `python -c "import app"` succeeds from `backend/`.
- `pnpm --dir frontend build` succeeds.

**Do not change:**
- `AGENTS.md`, `README.md`, `memory-bank/**`, `skills/**`, `docs/**`.

**Estimated agent time:** 10 min.

---

## Phase 1 — Backend bootstrap

**Goal:** runnable FastAPI app with health check and structured config.

**Dependencies:** Phase 0.

**Steps:**
- Add `fastapi`, `uvicorn[standard]`, `pydantic-settings`, `python-dotenv` to `backend/pyproject.toml`.
- Implement `app/core/config.py` (Pydantic `BaseSettings`, reads `.env`).
- Implement `app/main.py` with `app = FastAPI()` and `GET /health` returning `{"status": "ok"}`.

**Acceptance criteria:**
- `uvicorn app.main:app` starts without error.
- `curl localhost:8000/health` returns HTTP 200 with `{"status":"ok"}`.

**Do not change:** frontend, any auth/PHI logic (does not exist yet).

**Estimated agent time:** 10 min.

---

## Phase 2 — Database & migrations

**Goal:** PostgreSQL connection, SQLAlchemy session, Alembic initialised.

**Dependencies:** Phase 1.

**Steps:**
- Add `sqlalchemy`, `asyncpg`, `alembic` to backend deps.
- Add `docker-compose.yml` at repo root with a `postgres:16` service (port 5432, volume `glucochef_pg`).
- Implement `app/db/session.py` (async engine + session factory) and `app/db/base.py` (declarative base).
- Run `alembic init alembic` inside `backend/`; configure `env.py` to import `Base.metadata`.

**Acceptance criteria:**
- `docker compose up -d postgres` runs healthy.
- `alembic upgrade head` exits 0 (no migrations yet).
- `python -c "from app.db.session import engine; print(engine.url)"` prints the configured URL.

**Do not change:** `app/main.py` business logic, frontend.

**Estimated agent time:** 15 min.

---

## Phase 3 — Core ERD models

**Goal:** SQLAlchemy models for `Patient`, `NutritionalProfile`, `RejectedIngredient`, `LabResult`, `Suggestion`, `Recipe`, `AuditLogEntry`.

**Dependencies:** Phase 2.

**Steps:**
- Create `app/models/` with one file per entity.
- All PHI-bearing columns (lab values, medications, allergies) typed as `EncryptedString` placeholder (real encryption added in Phase 5).
- Generate initial Alembic migration: `alembic revision --autogenerate -m "init schema"`.

**Acceptance criteria:**
- `alembic upgrade head` applies the migration without error.
- `psql` shows all 7 tables with correct foreign keys (`patient_id` references on PHI tables).
- Pytest fixture can insert a `Patient` row.

**Do not change:** API routes (none exposed yet), frontend.

**Estimated agent time:** 15 min.

---

## Phase 4 — Cognito JWT auth dependency

**Goal:** FastAPI dependency that validates Cognito JWTs and resolves the current `Patient`.

**Dependencies:** Phase 3.

**Steps:**
- Add `python-jose[cryptography]`, `httpx` to deps.
- Implement `app/core/security.py::get_current_patient` — verifies Cognito JWT against the user pool's JWKS.
- Add `COGNITO_USER_POOL_ID`, `COGNITO_REGION`, `COGNITO_APP_CLIENT_ID` to `config.py`.

**Acceptance criteria:**
- Unit test mocks JWKS and asserts: valid token → returns `Patient`; invalid signature → HTTP 401; expired → HTTP 401.
- `GET /me` (added as a one-line protected route) returns the patient's id when called with a valid token.

**Do not change:** models, db schema.

**Estimated agent time:** 15 min.

---

## Phase 5 — PHI encryption + audit log middleware

**Goal:** field-level AES-256 on PHI columns and an audit log row per PHI read/write.

**Dependencies:** Phase 4.

**Steps:**
- Add `cryptography` dep. Implement `app/core/crypto.py::EncryptedString` as a SQLAlchemy `TypeDecorator` using Fernet (AES-128-CBC + HMAC; acceptable as "AES-256-equivalent" per HIPAA practice baseline — record decision in `memory-bank/decisions.md`).
- Replace placeholder `EncryptedString` in Phase 3 models with this real implementation.
- Implement `app/core/audit.py` — context-managed helper that writes `AuditLogEntry(actor_id, action, resource, timestamp)`.
- Wrap PHI routes (added in later phases) with the audit helper via a FastAPI dependency.

**Acceptance criteria:**
- Pytest: writes a `LabResult`, reads the raw row via `text("SELECT ...")`, asserts ciphertext ≠ plaintext.
- Pytest: a PHI route call produces exactly one `audit_log_entries` row with the correct actor and action.

**Do not change:** Cognito logic, frontend.

**Estimated agent time:** 15 min.

---

## Phase 6 — Onboarding API

**Goal:** `POST /onboarding` accepts diabetes type, medications, allergies, intolerances, rejected foods, cultural preferences and persists a `NutritionalProfile`.

**Dependencies:** Phase 5.

**Steps:**
- Define Pydantic request/response schemas in `app/schemas/onboarding.py`.
- Implement `app/api/routes/onboarding.py::create_profile` (protected, audited).
- Register router in `app/main.py`.

**Acceptance criteria:**
- Pytest: authenticated POST creates a profile and returns 201 with the profile id.
- Pytest: unauthenticated POST returns 401.
- Pytest: posting twice for the same patient updates (does not duplicate) the profile.

**Do not change:** lab or recipe endpoints.

**Estimated agent time:** 10 min.

---

## Phase 7 — Rejected ingredient persistence

**Goal:** `POST /ingredients/{name}/reject` persists a rejection; rejected items are excluded from future suggestions.

**Dependencies:** Phase 6.

**Steps:**
- Implement endpoint + `RejectedIngredient` repository helper `is_rejected(patient_id, ingredient)`.
- Add unique constraint `(patient_id, ingredient_normalized)`.

**Acceptance criteria:**
- Pytest: rejecting "salmón" then rejecting "Salmón " (with whitespace/case) results in a single row.
- Pytest: `is_rejected` returns `True` for the rejected ingredient and `False` otherwise.

**Do not change:** onboarding endpoint, models from earlier phases (only add).

**Estimated agent time:** 10 min.

---

## Phase 8 — AI provider abstraction

**Goal:** single interface `app/ai/provider.py::AIProvider` with one concrete implementation (OpenAI **or** Claude, decide and document).

**Dependencies:** Phase 5.

**Steps:**
- Add chosen SDK to deps (`openai` or `anthropic`).
- Implement `AIProvider.suggest_alternatives(ingredient, profile, excluded) -> list[Alternative]` and `AIProvider.generate_recipe(accepted_ingredients, profile, latest_labs) -> Recipe`.
- Log every prompt + response (with PHI **redacted**) to `memory-bank/ai-usage-notes.md`.
- Add `AI_PROVIDER`, `AI_API_KEY`, `AI_MODEL` to `config.py`.

**Acceptance criteria:**
- Pytest with a mocked HTTP client asserts the prompt structure includes the patient's allergies and excludes rejected ingredients.
- A redacted prompt sample appears in `memory-bank/ai-usage-notes.md`.

**Do not change:** any route or model. Provider is internal-only at this phase.

**Estimated agent time:** 15 min.

---

## Phase 9 — Suggestion endpoint

**Goal:** `POST /suggestions` returns 3–4 nutritionally equivalent alternatives for a given ingredient, respecting profile and rejections.

**Dependencies:** Phases 6, 7, 8.

**Steps:**
- Implement `app/api/routes/suggestions.py` calling `AIProvider.suggest_alternatives`.
- Always return between 3 and 4 alternatives; if AI returns fewer, raise HTTP 502 (do **not** silently pad).

**Acceptance criteria:**
- Pytest with mocked provider: response contains 3–4 items, none of them in the patient's rejected list.
- Pytest: response excludes any ingredient matching a declared allergy.

**Do not change:** AI provider internals, models.

**Estimated agent time:** 10 min.

---

## Phase 10 — Recipe generation endpoint

**Goal:** `POST /recipes` builds a recipe from accepted ingredients and the latest labs.

**Dependencies:** Phases 8, 9, 11 (lab read).

> Soft dependency on Phase 11: if labs do not yet exist for a patient, the endpoint passes `latest_labs=None` to the provider.

**Steps:**
- Implement endpoint that calls `AIProvider.generate_recipe`.
- Persist the resulting `Recipe` linked to the patient.

**Acceptance criteria:**
- Pytest: response includes `title`, `ingredients`, `steps`, `nutrition_summary`.
- Pytest: when `latest_labs` shows red-flag HbA1c, the prompt sent to the provider includes a tightened carb constraint (assert on the captured prompt).

**Do not change:** suggestion endpoint.

**Estimated agent time:** 15 min.

---

## Phase 11 — Lab registration endpoint

**Goal:** `POST /labs` accepts HbA1c, fasting glucose, total cholesterol, triglycerides with units and date.

**Dependencies:** Phase 5.

**Steps:**
- Pydantic schema validates ranges (e.g., HbA1c 3–20%).
- Persist `LabResult` (encrypted), write audit entry.

**Acceptance criteria:**
- Pytest: valid payload → 201; out-of-range payload → 422.
- Pytest: stored value round-trips through encryption.

**Do not change:** recipe or suggestion endpoints.

**Estimated agent time:** 10 min.

---

## Phase 12 — Traffic-light evaluation

**Goal:** `GET /labs/trends` returns the lab history with `status: green|amber|red` per data point and an overall trend (`improving|stable|worsening`).

**Dependencies:** Phase 11.

**Steps:**
- Implement pure function `app/services/labs.py::evaluate(value, kind) -> Status` with thresholds documented in code comments and sourced from standard clinical ranges (ADA guidelines for HbA1c).
- Implement trend computation over the latest 3 entries.

**Acceptance criteria:**
- Pytest table-test covers green/amber/red for each lab type.
- Pytest: 3 worsening HbA1c entries → trend = `worsening`.

**Do not change:** lab write endpoint, encryption.

**Estimated agent time:** 15 min.

---

## Phase 13 — Diet–clinical correlation

**Goal:** suggestion and recipe prompts include the latest traffic-light state and tighten guidance for red states.

**Dependencies:** Phases 9, 10, 12.

**Steps:**
- Add `app/services/recommendations.py::build_clinical_context(patient_id)` returning a small dict consumed by the AI provider.
- Wire it into `suggest_alternatives` and `generate_recipe` call sites.

**Acceptance criteria:**
- Pytest: with HbA1c red, the prompt contains the string `"limit refined carbs"` (or equivalent constant defined in the module).
- Pytest: with all greens, the prompt omits any tightening clause.

**Do not change:** lab evaluation thresholds, models.

**Estimated agent time:** 10 min.

---

## Phase 14 — Frontend bootstrap & API client

**Goal:** typed API client in the Next.js app, `.env.local` wiring, basic layout.

**Dependencies:** Phase 1.

**Steps:**
- Add `frontend/src/lib/api.ts` (fetch wrapper with auth header injection).
- Add `NEXT_PUBLIC_API_URL` to `.env.local.example`.
- Replace default Next.js landing page with a minimal `app/page.tsx` (mobile-first Tailwind layout).

**Acceptance criteria:**
- `pnpm --dir frontend build` succeeds.
- Manual: `pnpm --dir frontend dev` renders the landing page at `localhost:3000`.

**Do not change:** backend.

**Estimated agent time:** 10 min.

---

## Phase 15 — Cognito sign-in UI

**Goal:** sign-up, confirm, sign-in flows backed by AWS Cognito (Amplify Auth or `oidc-client-ts`).

**Dependencies:** Phases 4, 14.

**Steps:**
- Add `aws-amplify` to frontend deps and configure with Cognito pool id + client id.
- Implement `/sign-in`, `/sign-up`, `/confirm` routes.
- Store the JWT in memory + `httpOnly` cookie via a Next.js Route Handler (no `localStorage`).

**Acceptance criteria:**
- Manual: a new user can sign up, confirm via email, and sign in.
- Playwright smoke test stubs Cognito and asserts redirect from `/sign-in` to `/onboarding`.

**Do not change:** backend auth dependency.

**Estimated agent time:** 15 min.

---

## Phase 16 — Onboarding UI

**Goal:** multi-step form posting to `POST /onboarding`.

**Dependencies:** Phases 6, 15.

**Steps:**
- Implement `/onboarding` with steps: diagnosis → medications → allergies/intolerances → rejected foods → preferences.
- Use `react-hook-form` + `zod`.

**Acceptance criteria:**
- Playwright test fills all steps and asserts a 201 from the backend (mocked or real).
- Refresh mid-flow restores filled values (persist to `sessionStorage`).

**Do not change:** API contract from Phase 6.

**Estimated agent time:** 15 min.

---

## Phase 17 — Suggestion & rejection UI

**Goal:** suggestion screen calling `POST /suggestions`, with accept/reject buttons that hit `POST /ingredients/{name}/reject`.

**Dependencies:** Phases 7, 9, 16.

**Steps:**
- `/suggestions` route, mobile-first card layout, optimistic rejection.

**Acceptance criteria:**
- Playwright test: reject an item → it disappears and is not returned by the next mocked call.

**Do not change:** onboarding UI.

**Estimated agent time:** 10 min.

---

## Phase 18 — Recipe view

**Goal:** `/recipes/new` triggers `POST /recipes`, `/recipes/[id]` renders the result.

**Dependencies:** Phases 10, 17.

**Steps:**
- Render title, ingredient list, step-by-step instructions, nutrition summary.

**Acceptance criteria:**
- Playwright test: from suggestion screen, accept ingredients → recipe page renders all four blocks.

**Do not change:** suggestion UI.

**Estimated agent time:** 10 min.

---

## Phase 19 — Lab entry UI

**Goal:** `/labs/new` form posting to `POST /labs`.

**Dependencies:** Phases 11, 15.

**Steps:**
- Form with the four canonical lab fields, date picker, unit selector.

**Acceptance criteria:**
- Playwright test: submitting invalid HbA1c shows an inline error; submitting valid values returns to `/labs`.

**Do not change:** backend lab schema.

**Estimated agent time:** 10 min.

---

## Phase 20 — Lab trends UI

**Goal:** `/labs` shows traffic-light cards per lab kind and a sparkline of the last 6 entries.

**Dependencies:** Phases 12, 19.

**Steps:**
- Use `recharts` or `visx` for the sparkline.
- Plain-language interpretation string under each card (sourced from a constant map).

**Acceptance criteria:**
- Playwright test: with seeded data, three cards render with the correct colour class.

**Do not change:** lab entry UI.

**Estimated agent time:** 15 min.

---

## Phase 21 — PWA manifest & service worker

**Goal:** the app installs from the browser with a splash screen and home-screen icon.

**Dependencies:** Phase 14.

**Steps:**
- Add `next-pwa` (or App Router-compatible equivalent) and a `public/manifest.webmanifest`.
- Provide 192px and 512px icons under `public/icons/`.
- Register service worker with a cache-first strategy for static assets only (no PHI caching).

**Acceptance criteria:**
- Lighthouse PWA audit in CI reaches the installability threshold.
- Manual: Chrome on Android shows the install prompt.

**Do not change:** any data-fetching path; the service worker must not cache `/labs`, `/recipes`, `/suggestions`, `/onboarding`.

**Estimated agent time:** 15 min.

---

## Phase 22 — Backend test suite hardening

**Goal:** pytest coverage ≥ 80% on `app/services` and `app/api/routes`.

**Dependencies:** Phases 6–13.

**Steps:**
- Add `pytest-cov`, `pytest-asyncio`, `httpx`.
- Add `make test` target running `pytest --cov=app --cov-fail-under=80`.

**Acceptance criteria:**
- `make test` exits 0 locally and in CI.

**Do not change:** production code (refactor only if a test reveals a defect — record in PR description).

**Estimated agent time:** 15 min.

---

## Phase 23 — Playwright E2E suite

**Goal:** one happy-path E2E test covering onboarding → suggestion → recipe and one covering labs → trends.

**Dependencies:** Phases 17, 18, 20.

**Steps:**
- `pnpm --dir frontend add -D @playwright/test`.
- Configure `playwright.config.ts` against `localhost:3000` with a backend test-stub.

**Acceptance criteria:**
- Both E2E specs pass headless in under 60 s combined.

**Do not change:** UI components (only test code).

**Estimated agent time:** 15 min.

---

## Phase 24 — GitHub Actions CI

**Goal:** CI runs backend tests, frontend build, frontend E2E, Lighthouse PWA audit on every PR.

**Dependencies:** Phases 22, 23.

**Steps:**
- `.github/workflows/ci.yml` with jobs: `backend-tests`, `frontend-build`, `frontend-e2e`, `lighthouse`.
- Cache `pip` and `pnpm` stores.

**Acceptance criteria:**
- A dummy PR triggers all four jobs green.

**Do not change:** test code, application code.

**Estimated agent time:** 15 min.

---

## Phase 25 — AWS Free Tier deployment

**Goal:** public URL serving the PWA, backed by RDS PostgreSQL and the FastAPI service.

**Dependencies:** Phase 24.

**Steps:**
- Provision RDS `db.t3.micro`, an ECS Fargate service (or App Runner) for the backend, and Amplify Hosting (or S3+CloudFront) for the frontend.
- Configure Cognito user pool in the same region.
- Add `.github/workflows/deploy.yml` triggered on push to `main`.

**Acceptance criteria:**
- Public URL responds 200 on `/` and `/health` (proxied).
- An external evaluator can sign up, onboard, log a lab, and view a recipe end-to-end.

**Do not change:** application code; this phase is infra-only.

**Estimated agent time:** 15 min (assuming AWS credentials and IaC scaffolding are pre-provided; otherwise split into 25a/25b).

---

## Non-goals

The following are **explicitly out of scope** for the MVP delivered through phases 0–25. An agent that proposes any of these must stop and flag the request for human review.

- **PDF lab parsing or OCR.** Labs are entered through the guided form only.
- **Full 7-day or weekly meal planning.** Recipes are generated one at a time on demand.
- **Learning loop / personalised ranking.** Rejection only filters; no model fine-tuning, no embedding store, no rating signals.
- **Shopping list generation.** May be revisited post-MVP if budget allows; not part of these phases.
- **Multi-user roles** (nutritionist or physician view), team accounts, family sharing.
- **Native iOS or Android apps.** PWA only; no React Native, no Capacitor, no App Store distribution.
- **Glucometer or CGM integrations** (Dexcom, LibreLink, Accu-Chek, etc.).
- **Payments, subscriptions, or paywalls.**
- **Real-time chat with clinicians.**
- **Push notifications, email digests, or SMS reminders.**
- **i18n beyond the patient-facing Spanish UI copy.** Repo artifacts (code, docs, tests, commits) stay in English per `AGENTS.md`.
- **Formal HIPAA certification.** The product demonstrates HIPAA-aligned practices; certification is not pursued.
- **Multi-region or multi-cloud deployment.** Single AWS region, Free Tier only.
- **Custom design system.** Tailwind + minimal primitives; no Storybook, no component library extraction.
- **Analytics, A/B testing, or feature flags.**
- **Admin dashboard or back-office UI.**

---

## Global "Do not change" — applies to every phase

- `AGENTS.md`, `CLAUDE.md`, `README.md`.
- Anything under `memory-bank/` except `memory-bank/decisions.md` (append-only) and `memory-bank/ai-usage-notes.md` (append-only).
- Anything under `skills/` and `.windsurf/skills/`.
- The product scope captured in `/docs/product-doc.md`. If a phase reveals a scope conflict, stop and surface it; do not edit the product doc unilaterally.
- The stack invariants table at the top of this PRD.
