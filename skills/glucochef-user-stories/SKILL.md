---
name: glucochef-user-stories
description: Write, expand, review, or refine user stories for the GlucoChef project. Use this skill whenever the user asks to create, update, or critique user stories, acceptance criteria, or story maps for any GlucoChef feature — even if they phrase it as "write the stories for Phase X", "add acceptance criteria", "break this epic down", or "check if this story is well-formed". Always consult this skill before writing any GlucoChef story or acceptance criterion.
---

# User Story Writing Guide

## Purpose

This skill governs how user stories are written for GlucoChef across all four documentation artifacts in Delivery 1 (May 27, 2026). It encodes the project's scope decisions, domain language, and quality bar so that every story a coding agent or reviewer encounters is consistent, unambiguous, and directly traceable to a phase in the Agent-Optimised PRD.

**Source of truth:**
- `docs/product-doc.md` — MVP scope, personas, success criteria, non-functional requirements.
- `docs/glucochef-prd.md` — Phase-by-phase acceptance criteria (Phases 0–25).

If a story conflicts with either document, the story is wrong — flag it rather than adjusting the document.

---

## 1. Canonical Persona

GlucoChef MVP has **one primary persona** for story authorship:

| Token | Description |
|---|---|
| `Patient` | Adult (18+) with Type 1, Type 2, or gestational diabetes. Maps to María, 47, the reference persona in `product-doc.md §3.1`. |

> **Do not write stories for the Nutritionist or Physician personas.** Those roles are deferred to v2 (`product-doc.md §3.2`). If a story's actor is not `Patient`, it belongs in the deferred backlog and must be explicitly labelled `[v2]`.

---

## 2. Story Format

Every story follows this exact template:

```
**US-[ID]: [Short imperative title]**
Epic: [Epic name from §4]
Phase: [PRD phase number(s) this story maps to]

As a Patient,
I want to [action],
so that [outcome tied to a real patient need].

**Acceptance Criteria**

Scenario: [Happy path — one-line description]
  Given [the initial state or precondition]
  When  [the patient performs an action]
  Then  [the observable outcome]

Scenario: [Edge case or error path]
  Given [the initial state or precondition]
  When  [the action that triggers the error or boundary]
  Then  [the system's observable response]

**Notes** *(optional)*
- [Edge case, dependency, deferral note, or design constraint]
```

### Gherkin rules

- **One scenario per distinct path** — happy path and at least one error or boundary scenario per story.
- **Given** sets up state that exists *before* the action. Use past tense: "the Patient has completed onboarding", "the lab entry form is open".
- **When** is a single action the Patient or system performs. One `When` per scenario — split if two actions are needed.
- **Then** is the single observable outcome. If multiple things change, use `And` continuations:
  ```
  Then  the traffic-light card shows amber
  And   the trend direction reads "worsening"
  ```
- **And / But** extend the nearest step. `But` is reserved for negations: `But the rejected ingredient does not reappear`.
- Scenarios map 1-to-1 to Playwright steps or Pytest parameterised cases. Write them so a developer can translate them directly without interpretation.
- Do **not** name libraries, endpoints, or database tables inside Gherkin steps — those are implementation details.

### ID format
`US-[two-digit sequence]-[epic-abbreviation]`
Examples: `US-01-ONB`, `US-07-SUG`, `US-14-LAB`

Epic abbreviations:

| Epic | Abbreviation |
|---|---|
| Authentication & Onboarding | ONB |
| Ingredient Suggestions | SUG |
| Recipe Generation | RCP |
| Lab Results | LAB |
| Diet–Clinical Correlation | COR |
| PWA & Mobile Experience | PWA |
| Security & Compliance | SEC |

---

## 3. Quality Rules

Apply all rules before marking a story ready. A story fails review if any rule is violated.

### 3.1 INVEST checklist

| Letter | Rule | Common failure |
|---|---|---|
| **I**ndependent | Story can be built and tested without completing another story in the same sprint | Coupling to an unbuilt endpoint not in its declared phase dependencies |
| **N**egotiable | Acceptance criteria describe *what*, not *how* | AC says "use Fernet encryption" instead of "PHI is unreadable in raw DB rows" |
| **V**aluable | Outcome clause names a concrete patient benefit | "so that the system stores the data" — no patient value stated |
| **E**stimable | Scope is narrow enough to size | Epic-sized stories must be split |
| **S**mall | Completable in one phase (5–15 min agent time per PRD) | Story spans more than two PRD phases |
| **T**estable | Every AC can be verified by a Pytest assertion or Playwright step | AC uses "should feel", "should be fast", "should be intuitive" |

### 3.2 Acceptance criteria rules

- ACs are written as **Gherkin scenarios** (see template in §2). Bullet-point ACs are not accepted.
- Each scenario is **binary pass/fail** — no partial credit, no "mostly works".
- Each `When` clause contains exactly **one** action. If two actions are needed, write two scenarios.
- `Then` clauses must be verifiable by a Playwright assertion, a Pytest assertion, a Lighthouse audit result, or a documented manual step (`Manual: <action> → <outcome>`). Avoid vague outcomes like "the page updates" or "it works".
- Scenarios must not embed implementation details (library names, SQL queries, AWS service names) unless the AC is explicitly about infrastructure (e.g., a Phase 25 deployment check).
- Every story must have **at least two scenarios**: one happy path and one error or boundary condition.

### 3.3 Scope guard

Before writing or approving any story, verify the feature is **in scope**:

**Allowed in MVP:**
- Nutritional onboarding (diabetes type, medications, allergies, intolerances, rejected foods, cultural preferences)
- Ingredient suggestion with 3–4 alternatives per ingredient
- On-demand recipe generation from accepted ingredients
- Manual lab entry (HbA1c, fasting glucose, total cholesterol, triglycerides)
- Traffic-light lab visualisation + trend charts
- Diet–clinical correlation (latest labs modulate AI prompt constraints)
- PWA install, full-screen experience, home-screen icon, splash screen
- HIPAA-aligned practices: AES-256 at rest, TLS in transit, RBAC, audit logs, explicit consent

**Explicitly out of scope — reject any story for these:**
- PDF lab parsing or OCR
- Full 7-day meal plan generation
- Learning loop / personalised ranking from ratings
- Shopping list generation
- Nutritionist or physician roles / RBAC expansion
- Native iOS or Android apps (React Native, Capacitor)
- Glucometer or CGM integrations
- Payments, subscriptions, or paywalls
- Push notifications, email digests, SMS reminders
- i18n beyond Spanish patient-facing copy
- Formal HIPAA certification
- Analytics, A/B testing, feature flags
- Admin dashboard or back-office UI

If a requested story touches an out-of-scope feature, write a one-line note: `[OUT OF SCOPE — deferred to v2: <reason>]` and do not draft the story.

---

## 4. Epic Map

Stories are organised under seven epics that map directly to PRD phases.

| Epic | PRD Phases | Core stories |
|---|---|---|
| **Authentication & Onboarding** | 4, 6, 15, 16 | Sign-up, email confirmation, sign-in, onboarding multi-step form |
| **Ingredient Suggestions** | 7, 9, 17 | Suggest alternatives, reject ingredient, persist rejections |
| **Recipe Generation** | 8, 10, 18 | Generate recipe from accepted ingredients, view recipe |
| **Lab Results** | 11, 12, 19, 20 | Log lab values, traffic-light status, trend chart |
| **Diet–Clinical Correlation** | 13 | Correlation signal in suggestions and recipes |
| **PWA & Mobile Experience** | 14, 21 | Install prompt, full-screen, home-screen icon, splash screen |
| **Security & Compliance** | 4, 5 | JWT auth, PHI encryption, audit log, consent |

---

## 5. Writing Process

Follow these steps in order when authoring a batch of stories.

### Step 1 — Scope check
Confirm the feature maps to an in-scope item in `product-doc.md §6.1`. If not, stop.

### Step 2 — Identify the PRD phase
Find the matching phase(s) in `glucochef-prd.md`. The phase's acceptance criteria are the **primary source** for the story's ACs — translate them from agent-facing language to patient-facing language where appropriate.

### Step 3 — Draft the story body
Write the "As a Patient, I want … so that …" clause. The outcome must name a benefit from the patient's perspective, not a system state.

**Good:** "so that I can see whether my HbA1c is improving without waiting for my next appointment."
**Bad:** "so that the system stores my lab entry with the correct timestamp."

### Step 4 — Draft acceptance criteria
Start from the PRD phase's acceptance criteria. Rewrite each one as an observable user-facing or system-observable condition. Add at least one negative/edge-case AC not already in the PRD.

### Step 5 — INVEST review
Run the §3.1 checklist mentally. If the story fails any letter, fix it before moving on.

### Step 6 — Assign ID and epic
Follow the ID format in §2.

### Worked example

```
**US-03-LAB: Log a lab entry with HbA1c and glucose values**
Epic: Lab Results
Phase: 11

As a Patient,
I want to manually enter my latest HbA1c and fasting glucose values,
so that I can track how my numbers evolve over time without needing my doctor
to interpret the results for me.

**Acceptance Criteria**

Scenario: Submitting valid lab values saves the entry and returns to the trends page
  Given the Patient is signed in and the lab entry form is open
  When  the Patient enters an HbA1c of 7.2% and a fasting glucose of 110 mg/dL
  And   the Patient selects today's date and taps Submit
  Then  the lab trends page shows the new entry with the correct values and date

Scenario: Submitting an out-of-range HbA1c value shows an inline validation error
  Given the Patient is signed in and the lab entry form is open
  When  the Patient enters an HbA1c of 25% (above the valid range of 3–20%)
  Then  an inline error appears on the HbA1c field
  And   the form does not submit

**Notes**
- Cholesterol and triglycerides are optional in this story; a separate story (US-04-LAB)
  covers the lipid panel fields.
- Range validation mirrors the Pydantic schema in Phase 11.
```

---

## 6. Domain Glossary

Use these terms consistently. Do not invent synonyms.

| Term | Definition |
|---|---|
| **Patient** | The primary persona. Use in story actor clause. Never "user", "diabetic", or "person". |
| **Nutritional profile** | The complete set of onboarding data: diabetes type, medications, allergies, intolerances, rejected foods, cultural preferences. |
| **Rejected ingredient** | An ingredient the patient has explicitly dismissed. Once rejected, it must never be re-suggested in the current MVP. |
| **Alternative** | One of the 3–4 nutritionally equivalent substitutes the AI suggests for a given ingredient. |
| **Lab entry** | A single manual submission of HbA1c, fasting glucose, total cholesterol, and triglycerides for a given date. |
| **Traffic-light status** | Green / amber / red classification per lab metric, derived from ADA-guideline thresholds. |
| **Trend** | Computed direction across the latest 3 lab entries: `improving`, `stable`, or `worsening`. |
| **Clinical context** | The structured summary of the patient's latest traffic-light states passed to the AI provider to modulate recipe and suggestion prompts. |
| **PHI** | Protected Health Information — lab values, medications, allergies, diagnoses. PHI fields are encrypted at rest. |

---

## 7. Anti-Patterns

These patterns are prohibited. If you see them in a draft, fix before delivery.

| Anti-pattern | Why it's wrong | Fix |
|---|---|---|
| AC says "the system should encrypt the data" | Implementation detail inside an AC | Write a Gherkin `Then` that PHI is unreadable when queried directly without the application key |
| Outcome clause says "so that the data is saved" | No patient value | Rewrite to name what the patient gains from having the data saved |
| Story covers two epics (e.g., onboarding + lab entry) | Violates Small and Independent | Split into two stories |
| Story references a v2 feature (PDF upload, meal plan, feedback loop) | Out of scope | Replace with `[OUT OF SCOPE]` note |
| AC is unverifiable: "the experience feels native" | Not testable | `Then the Lighthouse PWA audit returns an installability pass` |
| Story actor is "User" | Wrong persona token | Replace with "Patient" |
| Missing edge-case scenario | Incomplete contract | Add at least one error / boundary Gherkin scenario |
| ACs written as bullet checkboxes instead of Gherkin | Wrong format — cannot be translated to tests directly | Rewrite as `Scenario / Given / When / Then` |
| `When` has two actions: "When the Patient fills and submits the form" | Single-action rule violation | Split: one `When` for fill, separate scenario or `And` step for submit |
| `Then` names an internal component: "Then the `LabResult` table has a new row" | Implementation detail in a Then clause | Rewrite as an observable UI or API outcome: "Then the lab trends page shows the new entry" |

---

## 8. Reference: Phased Delivery Mapping

Stories for Delivery 1 (May 27, 2026) must cover **all PRD phases 0–25** at minimum at the epic level. The recommended minimum story count per epic:

| Epic | Minimum stories |
|---|---|
| Authentication & Onboarding | 5 |
| Ingredient Suggestions | 4 |
| Recipe Generation | 3 |
| Lab Results | 4 |
| Diet–Clinical Correlation | 2 |
| PWA & Mobile Experience | 2 |
| Security & Compliance | 3 |

Stories are delivered as a Markdown file at `docs/user-stories.md`. One H2 heading per epic, stories listed in ascending ID order within each epic.