# GlucoChef — Architecture Documentation

**Version:** 1.0 (MVP)
**Date:** May 2026
**Audience:** Technical academic evaluators, AI coding agents
**Status:** Baseline for Delivery 1 (Technical Documentation, May 27, 2026)

**Source of truth for scope:** `docs/product-doc.md`.
**Authoring rules:** `skills/glucochef-c4-architecture/SKILL.md`.

This folder is the structural and runtime view of GlucoChef. Each diagram answers exactly one question. Internal rules, thresholds, and business policies live in prose or in ADRs — never inside a diagram node.

---

## 1. System overview

GlucoChef is a single mobile-first Progressive Web App backed by a FastAPI service and a PostgreSQL database on AWS Free Tier. Authentication is delegated to AWS Cognito; ingredient alternatives and recipe text are produced by an external AI provider (OpenAI or Claude). All Protected Health Information (PHI) is encrypted at the field level before it reaches the database, and every PHI access is recorded in an append-only audit log.

The product is built around three principles encoded directly in the architecture:

1. **Dynamic alternatives, not a static catalog.** Suggestions are generated at request time by `Suggestion Service` calling the AI provider, then filtered by allergies and persisted rejections.
2. **Plain-language clinical data.** `Lab Service` computes traffic-light status and trend; the API never returns raw clinical interpretations the patient cannot read.
3. **Diet–clinical feedback loop.** `Correlation Policy` is a pure module that turns the latest traffic-light state into a constraint consumed by both `Suggestion Service` and `Recipe Service`.

---

## 2. Diagram index

The full LikeC4 model lives in [`glucochef.c4`](./glucochef.c4). Five views are exposed.

| View id | Level | Question answered |
|---|---|---|
| `l1_context` | C4-L1 | Who uses GlucoChef and which external systems does it depend on? |
| `l2_containers` | C4-L2 | Which runtime containers make up GlucoChef? |
| `l3_backend` | C4-L3 | How is the FastAPI backend structured internally? |
| `l3_frontend` | C4-L3 | How is the Next.js PWA structured internally? |
| `phi_boundary` | Cross-cutting | Which elements store or process PHI? |

Runtime flows complement the structural views and are kept as Mermaid sequence diagrams under [`sequences/`](./sequences/):

| File | Question answered |
|---|---|
| [`sequences/01-signup.md`](./sequences/01-signup.md) | How does a Patient create and confirm an account? |
| [`sequences/02-onboarding.md`](./sequences/02-onboarding.md) | How is the nutritional profile created with explicit consent? |
| [`sequences/03-ingredient-suggestion.md`](./sequences/03-ingredient-suggestion.md) | How are allergy- and rejection-aware alternatives produced? |
| [`sequences/04-recipe-with-correlation.md`](./sequences/04-recipe-with-correlation.md) | How does a red HbA1c tighten the next recipe? |
| [`sequences/05-lab-entry.md`](./sequences/05-lab-entry.md) | How is a lab entry stored, interpreted, and audited? |

Architecture decisions are kept in [`../decisions/`](../decisions/) as MADR records:

| ADR | Decision |
|---|---|
| [ADR-001](../decisions/ADR-001-pwa-over-native.md) | Ship as an installable PWA instead of native iOS/Android apps. |
| [ADR-002](../decisions/ADR-002-field-level-phi-encryption.md) | Encrypt PHI at the field level with AES-256-GCM, not only at the volume level. |
| [ADR-003](../decisions/ADR-003-manual-lab-entry.md) | Capture labs through a guided manual form; defer PDF parsing to v2. |
| [ADR-004](../decisions/ADR-004-ai-provider-abstraction.md) | Hide the LLM behind an internal port so OpenAI and Claude are interchangeable. |

---

## 3. How to render the diagrams

The `.c4` file is consumed by [LikeC4](https://likec4.dev). Local preview during authoring:

```sh
npx -y likec4 preview docs/architecture/glucochef.c4
```

Static export for the final delivery (PNG/SVG into `docs/architecture/exports/`):

```sh
npx -y likec4 export docs/architecture/glucochef.c4 --output docs/architecture/exports
```

Mermaid sequence diagrams render natively on GitHub and in any Markdown viewer that supports Mermaid; no toolchain is required to read them.

---

## 4. Trust boundary and PHI handling

The trust boundary encloses `PWA Frontend`, `Backend API`, and `PostgreSQL Database`. Cognito and the AI Provider sit outside it.

- **At rest.** PHI columns (allergies, intolerances, rejections, diagnosis, medications, lab values) are AES-256-GCM ciphertext written through `PHI Crypto Service`. The encryption key is sourced from AWS KMS and never reaches the PWA. Rationale and trade-offs are recorded in [ADR-002](../decisions/ADR-002-field-level-phi-encryption.md).
- **In transit.** TLS 1.2+ on every hop, including PWA → API and API → AI Provider.
- **At the AI boundary.** Prompts sent to the AI Provider include only de-identified profile fragments (allergens, intolerances, accepted ingredients, traffic-light state). Patient identifiers, raw lab values, and free-text notes never leave the trust boundary.
- **Auditing.** Every PHI read, write, and denied access produces a row in `Audit Log Service` with `(patient_id, action, resource, timestamp, outcome)`. The PWA cannot bypass it because the only path to PHI columns is through the FastAPI services.
- **Service Worker.** `PWA Shell & Service Worker` caches static assets only. Routes that render PHI are explicitly excluded from the cache so an offline device never displays stale clinical data.

The `phi_boundary` view in `glucochef.c4` is the canonical visual answer to *"which elements touch PHI?"*.

---

## 5. Scope discipline

Two containers are modelled with the `#deferred` tag and excluded from every MVP view: `PDF Lab Parser` and `Weekly Meal Planner`. They are kept in the model so reviewers can see the v2 surface, but the MVP architecture does not depend on them. See [ADR-003](../decisions/ADR-003-manual-lab-entry.md) for the rationale on lab capture.

---

## 6. Non-functional posture

| Concern | Approach |
|---|---|
| Cost ceiling | AWS Free Tier only: t3.micro RDS, single Uvicorn worker behind API Gateway / Lambda or a small EC2 instance, Cognito free tier. |
| Deployability | One PWA, one API, one DB. GitHub Actions builds, runs Pytest + Playwright, and deploys on push to `main`. |
| Observability | Application logs (no PHI in log lines) and the audit log table. CloudWatch retention bounded to the documented PHI retention window. |
| Resilience | The MVP is single-region and best-effort. Failure modes are surfaced to the patient as inline errors; degraded AI responses fall back to a "try again" state rather than padding suggestions. |
| Reversibility | The AI Provider is hidden behind an internal port (ADR-004), so swapping OpenAI for Claude is a configuration change, not an architectural change. |

---

## 7. References

- `docs/product-doc.md` — product scope, success criteria, NFRs.
- `docs/user-stories.md` — Gherkin acceptance criteria the architecture must satisfy.
- `skills/glucochef-conventions/SKILL.md` — stack, MVP scope, security baseline, terminology.
- `skills/glucochef-c4-architecture/SKILL.md` — diagram rules and templates this folder follows.
