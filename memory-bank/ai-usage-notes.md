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
