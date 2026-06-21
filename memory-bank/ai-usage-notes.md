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
