---
name: glucochef-product-doc
description: >
  Produce or update the GlucoChef Product Document — the authoritative
  single-source-of-truth artifact that captures product vision, problem
  statement, target users, MVP scope, deferred features, success criteria,
  and non-functional requirements. Use this skill whenever the user asks to
  write, draft, update, review, or iterate on the GlucoChef product doc,
  product requirements document (PRD), or product brief. Also triggers for
  questions like "what does the product doc need?", "what sections should we
  include?", or "help me write the product documentation for GlucoChef".
---

# Product Document Skill

Guides the creation and maintenance of the **GlucoChef Product Document**.

Before writing any section, confirm you have read (in this session):

1. `AGENTS.md` — language rule, repo structure, commit conventions.
2. `skills/glucochef-conventions/SKILL.md` — confirmed stack, MVP scope,
   deferred features, product principles, clinical terminology.

Do not re-derive or duplicate any decision already captured there.

---

## Document Purpose

The product doc is written for a **technical academic audience** who need to understand:

1. What problem GlucoChef solves and why existing solutions fall short.
2. Who the target user is and what their real pain points are.
3. Exactly what is in the MVP and what is explicitly deferred — and why.
4. How success is measured.
5. Non-functional constraints that shape architecture decisions downstream.

It is **not** a marketing document. Precision and justification matter more
than persuasion.

---

## Required Sections

Produce all sections below, in order. Each section heading is the canonical
English title to use in the document.

### 1. Executive Summary
One paragraph (≤150 words). States the problem, the solution, and the
primary users. Written last but placed first.

### 2. Problem Statement
Three distinct problem dimensions, each with a short title and 2–4
sentences of elaboration:

- **Generic nutrition advice** — static recipe catalogs ignore allergies,
  preferences, and individual clinical context.
- **Disconnected lab results** — patients receive HbA1c and other values as
  opaque numbers with no actionable dietary guidance.
- **No diet–clinical feedback loop** — food choices and lab trends live in
  separate worlds; no existing app bridges them for diabetes patients.

Support each dimension with at least one concrete data point or user quote
from the competitive research (see `references/context.md §Research`).

### 3. Target Users

#### 3.1 Primary
Adult patients (18+) managing Type 1, Type 2, or gestational diabetes who
want to improve nutrition and understand their lab results. Include a
**persona snapshot** — one representative fictional user with name, age,
diagnosis, and key frustration.

#### 3.2 Secondary (out of MVP scope)
Nutritionists and physicians seeking remote diet/clinical monitoring for
their patients. State explicitly: **out of scope for MVP**.

### 4. Competitive Landscape
A brief table or structured comparison covering: mySugr, Glucose Buddy,
Klinio, and CGM apps (Dexcom / LibreLink). Columns: App · Focus · Key Gap.
Close with a **gap statement**: no existing solution integrates personalised
nutrition + lab tracking + diet–clinical correlation in one place.

### 5. Product Vision
One sentence. Format: *"For [user] who [need], GlucoChef is a [category]
that [key benefit], unlike [alternatives] which [limitation]."*

### 6. MVP Feature Scope

#### 6.1 In Scope
List each feature with a one-sentence description and the user value it
delivers. Canonical MVP features:

| Feature | Description | User Value |
|---|---|---|
| Nutritional Onboarding | Captures diabetes type, medications, allergies, intolerances, rejected foods, cultural preferences | Personalises every downstream recommendation |
| Ingredient Suggestion Engine | AI proposes 3–4 nutritionally equivalent alternatives per ingredient; rejected items are never re-suggested | Eliminates one-size-fits-all dietary advice |
| On-Demand Recipe Generation | Recipes built from accepted ingredients, not a static catalogue | Patient eats food they actually like |
| Lab Result Registration | Guided form for HbA1c, fasting glucose, cholesterol, triglycerides; manual entry only in MVP | Structured capture of clinical data |
| Lab Trend Visualisation | Traffic-light system (green/yellow/red) with plain-language interpretation and trend charts | Patient understands their own numbers |
| Diet–Clinical Correlation | Clinical values feed back into nutritional recommendations (e.g., rising HbA1c tightens carb guidance) | Closes the gap between diet and lab outcomes |
| PWA / Mobile-First Experience | Installable from browser, no-address-bar, splash screen, home screen icon | Native app feel without App Store friction |
| HIPAA-Aligned Data Practices | AES-256 at rest for PHI fields, TLS 1.2+ in transit, RBAC, audit logs, explicit user consent | Demonstrates health data stewardship |

#### 6.2 Deferred to v2
List with one-line rationale for each deferral:

| Feature | Deferral Rationale |
|---|---|
| PDF Lab Result Upload | Lab PDF formats vary significantly; parsing risk exceeds timeline budget |
| Full 7-Day Meal Plan | Multi-day nutritional balancing increases complexity; MVP generates individual recipes |
| Intelligent Feedback Loop | Learning from rejections/ratings requires data accumulation; MVP filters without learning |
| Shopping List Generation | Low-effort stretch goal; included only if time allows after core features |
| Multi-user Roles (nutritionist view) | Requires RBAC expansion and a separate UX track; deferred to v2 |

### 7. Success Criteria
Map directly to the business brief's acceptance criteria:

1. A patient can register, set up their profile, receive ingredient
   suggestions with alternatives, and view generated recipes.
2. A patient can log lab values and see trends with clear visual interpretation.
3. Food recommendations reflect both the patient's profile and their clinical
   values.
4. The app installs from the browser and behaves like a native app (PWA).
5. Health data is protected with encryption and access audit logging.

For each criterion, add one measurable signal (e.g., "E2E Playwright test
passes the full onboarding-to-recipe flow").

### 8. Non-Functional Requirements

| Requirement | Target | Rationale |
|---|---|---|
| Infrastructure cost | AWS Free Tier only | Academic project budget constraint |
| Deployment | Public URL with CI/CD pipeline | Evaluator access required |
| HIPAA alignment | No formal certification; must demonstrate core practices | Academic scope |
| Mobile experience | PWA, no App Store | Web-stack continuity; no native build pipeline |
| Observability | Access audit logs for PHI | HIPAA-aligned practice |

### 9. Constraints & Risks

| Constraint / Risk | Mitigation |
|---|---|
| 30-hour total build budget | Explicit scope cuts (PDF parsing, meal planning, feedback loop) |
| PDF lab parsing complexity | Deferred; replaced by guided manual entry form |
| Single-developer team | Sequential delivery plan with clear milestones |
| AWS Free Tier limits | Architecture sized to stay within tier (RDS t3.micro, minimal Lambda) |

### 10. Delivery Milestones

| # | Deliverable | Date | Contents |
|---|---|---|---|
| 1 | Technical Documentation | May 27, 2026 | Product doc, user stories, C4 architecture, ERD |
| 2 | Functional Code | Jun 24, 2026 | Backend, frontend, AI integration, test suite |
| 3 | Deployed Product | Jul 14, 2026 | CI/CD pipeline, public URL, final docs, AI usage log |

---

## Writing Rules

- **Language**: English throughout. Exception: patient-facing UI copy may
  use Spanish terms where no clean English equivalent exists, but surround
  it in the document with English context.
- **Tone**: Technical, precise, and concise. Avoid marketing language.
- **Tense**: Present tense for current decisions; future tense only for
  planned v2 work.
- **Tables vs prose**: Prefer tables for comparisons and feature lists;
  prose for rationale and narrative sections.
- **Length target**: 1,500–2,500 words for the full document body (excluding
  tables). Evaluators read many docs; respect their time.
- **No orphan bullets**: Every bullet or table row has enough context to
  stand alone. Avoid one-word bullets.

---

## Output Format

Produce the document as a single **Markdown file** (`docs/product-doc.md`)
unless the user explicitly requests a Word document. If `.docx` is needed,
consult the `docx` skill before generating.

Place the file at: `docs/product-doc.md` in the repository root.

---

## Checklist Before Delivering

- [ ] All 10 sections present and in order
- [ ] Executive Summary written after all other sections are complete
- [ ] MVP feature table includes all 8 canonical features
- [ ] Deferred features table includes all 5 items with rationale
- [ ] Success criteria are measurable (each has a testable signal)
- [ ] No marketing language or vague superlatives
- [ ] Tables render correctly in Markdown
- [ ] Word count is within the 1,500–2,500 word target
