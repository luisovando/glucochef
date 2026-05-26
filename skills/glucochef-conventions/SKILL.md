---
name: glucochef-conventions
description: Foundational product context and conventions for GlucoChef: stack decisions, MVP scope (included and deferred), product principles, security baseline, terminology, anti-patterns, and process discipline. Always consult this skill before generating or reviewing any GlucoChef artifact (Product Doc, user stories, architecture, ERD, code, tests, CI/CD) so all outputs stay consistent with decisions already made.
---

# GlucoChef — Product Conventions

This skill is the shared product baseline. Any other skill, document, or piece of code in GlucoChef must align with what is defined here. If a proposal contradicts these conventions, surface the conflict explicitly before proceeding.

## Project context

GlucoChef is a smart nutritional assistant for patients managing diabetes. It is the capstone project of a master's program, with three deliveries:

- **May 27, 2026** — Technical documentation (Product Doc, User Stories, C4 Architecture, ERD)
- **June 24, 2026** — Functional code (backend, frontend, AI integration, test suite)
- **July 14, 2026** — Deployed product (CI/CD, public URL, final documentation, AI usage log)

Total work budget: approximately 30 hours. Every technical or product decision must weigh effort against value within that budget. When a proposal threatens the budget, cut before adding.

## Confirmed stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python) |
| Frontend | Next.js 14 as a Progressive Web App (mobile-first, installable) |
| Database | PostgreSQL on AWS RDS |
| Authentication | AWS Cognito |
| AI | OpenAI / Claude API |
| CI/CD | GitHub Actions → AWS Free Tier |
| Testing | Pytest (backend), Playwright (E2E frontend) |

Any deviation from this stack requires explicit justification recorded in `memory-bank/decisions.md`.

## MVP scope

### Included

- Nutritional onboarding: medical profile, allergies, intolerances, rejected foods, cultural preferences
- Ingredient suggestion engine with equivalent alternatives (not a static catalog)
- On-demand recipe generation from accepted ingredients
- Manual lab tracking (HbA1c, glucose, cholesterol, triglycerides) with traffic-light visualization and trend charts
- Diet ↔ lab connection: clinical values influence recommendations
- HIPAA-aligned design (encryption, audit logs, RBAC) — without formal certification
- Installable PWA, splash screen, no browser chrome

### Deferred to v2 (do not implement in MVP)

- Lab PDF upload with automatic parsing
- Full 7-day meal planning (MVP generates individual recipes)
- Intelligent feedback loop (in MVP, rejection only filters the ingredient)
- Shopping list
- Multi-user with roles (nutritionist/physician view)

If a request involves anything deferred, restate that it is out of scope and propose the MVP alternative.

## Product principles (non-negotiable)

1. **Dynamic alternatives, not a static catalog.** Recommendations always offer 3-4 equivalent options that respect the patient's restrictions. Rejection persists across sessions.
2. **Plain language for clinical data.** Lab results are translated to traffic lights (green/amber/red) with explanations in non-clinical language.
3. **Diet-clinical connection.** If values worsen, recommendations adjust automatically; the two domains are not separate.
4. **Mobile-first always.** Any interface is designed for mobile first, then adapted to desktop.
5. **Minimum necessary PHI.** No sensitive information is stored beyond what is strictly required for the product.

## Security baseline (HIPAA-aligned, not certified)

- PHI encrypted at rest (AES-256 at the field level on sensitive columns)
- TLS 1.2+ in transit
- RBAC for every endpoint that accesses health data
- Audit log of PHI access (who, what, when)
- Explicit consent during onboarding
- Retention policy documented in the Product Doc

## Terminology

- **PHI** (Protected Health Information) — the patient's clinical data
- **Patient** — the primary user; never referred to as "user" or "customer" in product copy
- **Lab** — clinical lab results entered by the patient
- **Suggestion** — a recommendation with alternatives (not a "recipe"; the recipe is generated later from accepted ingredients)
- **Recipe** — a concrete preparation generated from ingredients the patient has accepted
- **Traffic light** — the green/amber/red visualization of a clinical value against its healthy range

## Anti-patterns to avoid

- Hardcoded recipes in a static catalog
- Endpoints returning PHI without auth + audit log
- Suggesting a single ingredient with no alternatives
- Showing labs in clinical terms without translation for the patient
- Designing screens desktop-first
- Implementing deferred features "because we can"
- Over-documenting beyond what the MVP requires (documentation also consumes from the 30h budget)

## Process discipline

- **OpenSpec for non-trivial features.** Features go through a change folder under `openspec/changes/` with proposal → specs → design → tasks before code is written. Small fixes or copy tweaks do not require this ceremony.
- **AI usage log is incremental.** Notes about prompts, decisions, and AI-assisted outputs are captured in `memory-bank/ai-usage-notes.md` continuously, not reconstructed at the end.
- **Trigger-based growth.** New folders or files appear in the repo only when there is real content for them. Empty scaffolding is avoided.

## Output conventions when generating documentation

When this skill (or a downstream skill) produces an artifact, the output must:

- Be written in English (the repo-wide language rule lives in `AGENTS.md`)
- Be concise, with no corporate filler
- Justify scope decisions when something from the brief is cut
- Explicitly mark what is out of MVP when relevant