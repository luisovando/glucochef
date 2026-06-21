# Product Document for Glucochef

**Version:** 1.0 (MVP)
**Date:** May 2026
**Audience:** Technical academic evaluators
**Status:** Baseline for Delivery 1 (Technical Documentation, May 27, 2026)

---

## 1. Executive Summary

Patients managing diabetes face two unsolved problems on the same day: deciding what to eat and understanding their lab results. Existing apps either track glucose in isolation (mySugr, Glucose Buddy, CGM apps) or push generic recipe catalogs (Klinio), and none of them connect diet decisions to clinical evolution. **GlucoChef** is a mobile-first Progressive Web App that builds a personalised nutritional profile per patient, suggests ingredients with equivalent alternatives that respect allergies and rejections, generates on-demand recipes from accepted ingredients, and interprets manually entered lab values through a traffic-light system whose readings feed back into the recommendations. The MVP targets adult patients with Type 1, Type 2, or gestational diabetes, runs on AWS Free Tier, and is built under a 30-hour budget with HIPAA-aligned data practices but without formal certification.

## 2. Problem Statement

### 2.1 Generic nutrition advice
Diabetes apps surface "diabetic recipes" from static catalogs that ignore allergies, food intolerances, cultural preferences, and what the patient actually likes. Klinio publishes meal plans without referencing the patient's clinical values, and mySugr's Pro nutrition feature is limited to meal photos with no personalisation logic (`memory-bank/product-context.md §1`). Reddit threads on `r/diabetes` and `r/diabetes_t2` repeatedly describe contradictory advice across forums, doctors, and apps, and the abandonment of plans that feel like total restriction rather than substitution (`memory-bank/product-context.md §2`).

### 2.2 Disconnected lab results
Patients receive HbA1c, fasting glucose, lipid panels, and triglycerides as a PDF every three to six months and cannot translate the numbers into concrete dietary action (`memory-bank/project-brief.md §Context`). None of the surveyed apps store or interpret lab values: mySugr only estimates HbA1c from glucose readings, Glucose Buddy focuses on real-time glucose, and CGM apps (Dexcom, LibreLink) display glucose curves with no clinical-result history.

### 2.3 No diet–clinical feedback loop
Even when a patient tracks both food and labs, the two domains live in separate apps and separate mental models. There is no product on the market that adjusts nutritional recommendations when HbA1c rises or lipids worsen. The market gap is documented in `memory-bank/product-context.md §3`: *"No app integrates in a single place: personalized nutrition for diabetic patients + lab tracking + correlation between what you eat and how your clinical indicators evolve."*

## 3. Target Users

### 3.1 Primary
Adult patients (18+) diagnosed with Type 1, Type 2, or gestational diabetes who want to improve their diet and understand their lab results without depending on a clinician for every decision.

**Persona snapshot — María, 47, Type 2 diabetes (4 years).** Recently elevated HbA1c (7.8%). Receives lab PDFs from her endocrinologist every three months and "doesn't know what the numbers mean for tomorrow's lunch". Lactose intolerant, dislikes fish, follows a Mexican home-cooking pattern. Has tried two diabetes apps and abandoned both: one was English-only with U.S. recipes, the other showed glucose graphs with no nutritional guidance. Frustration: *"I don't need another graph; I need to know what to put on the plate tonight."*

### 3.2 Secondary (out of MVP scope)
Nutritionists and treating physicians who would benefit from remote visibility into a patient's diet and labs. **Out of scope for MVP** — supporting a clinician role requires a second UX track and an expanded RBAC model; both are deferred to v2.

## 4. Competitive Landscape

| App | Focus | Key Gap |
|---|---|---|
| mySugr (Roche) | Glucose tracking + bolus calculator, gamified | Locked to Accu-Chek devices; nutrition limited to meal photos; no lab tracking |
| Glucose Buddy (Azumio) | CGM/Fitbit integration, AI "Meal IQ" for glucose response | Up to $59.99/month; ad-heavy free tier; no lab tracking |
| Klinio | Meal plans and recipes for Type 2 diabetes | Generic plans; ignores patient lab values; no allergy/rejection persistence |
| Dexcom / LibreLink (CGM) | Real-time glucose curves | No nutrition module; no lab history; no diet–clinical correlation |

**Gap statement.** No surveyed product combines personalised nutrition (with allergy- and rejection-aware alternatives), structured lab tracking, and an explicit diet ↔ clinical correlation in a single mobile-first experience. GlucoChef occupies that intersection.

## 5. Product Vision

*For adult patients managing diabetes who struggle to translate generic nutrition advice and opaque lab results into daily food decisions, **GlucoChef** is a mobile-first nutritional assistant that pairs personalised ingredient suggestions with traffic-light lab interpretation in a single feedback loop, unlike glucose trackers and recipe catalogs which treat diet and clinical data as separate problems.*

## 6. MVP Feature Scope

### 6.1 In Scope

| Feature | Description | User Value |
|---|---|---|
| Nutritional Onboarding | Captures diabetes type, medications, allergies, intolerances, rejected foods, and cultural preferences in a guided flow | Personalises every downstream recommendation from day one |
| Ingredient Suggestion Engine | AI proposes 3–4 nutritionally equivalent alternatives per ingredient; rejected items are persisted and never re-suggested | Replaces one-size-fits-all advice with substitutions the patient will actually use |
| On-Demand Recipe Generation | Recipes are generated from the ingredients the patient has accepted, not from a static catalog | Patient eats food they recognise and like, increasing adherence |
| Lab Result Registration | Guided manual entry form for HbA1c, fasting glucose, cholesterol, and triglycerides | Structured clinical data capture without depending on PDF parsing |
| Lab Trend Visualisation | Green/amber/red traffic-light readings with plain-language interpretation and trend charts over time | Patient understands their own numbers without a clinician in the loop |
| Diet–Clinical Correlation | Latest lab values modulate nutritional recommendations (e.g., rising HbA1c tightens carb-density guidance) | Closes the loop between what the patient eats and how their numbers evolve |
| PWA / Mobile-First Experience | Installable from the browser, full-screen (no address bar), splash screen, home-screen icon | Native-app feel without App Store friction or a separate build pipeline |
| HIPAA-Aligned Data Practices | AES-256 at rest on PHI fields, TLS 1.2+ in transit, RBAC on PHI endpoints, audit logs, explicit onboarding consent | Demonstrates health-data stewardship suitable for an academic deliverable |

### 6.2 Deferred to v2

| Feature | Deferral Rationale |
|---|---|
| PDF Lab Result Upload | Lab PDF formats vary significantly across providers; parsing risk and edge-case handling exceed the 30-hour budget |
| Full 7-Day Meal Plan | Multi-day nutritional balancing requires a separate optimisation layer; MVP generates individual recipes on demand |
| Intelligent Feedback Loop | Learning from rejections and ratings requires accumulated data and an evaluation harness; MVP only filters rejected ingredients |
| Shopping List Generation | Stretch goal with low clinical value relative to core features; included only if time remains after acceptance criteria are met |
| Multi-user Roles (nutritionist view) | Adds a second persona, RBAC expansion, and a dedicated UX track that does not fit the MVP timeline |

## 7. Success Criteria

Each criterion below maps to one acceptance criterion from `memory-bank/project-brief.md §Success criteria` and includes a measurable verification signal.

1. **End-to-end onboarding to recipe.** A patient can register, complete the onboarding profile, receive ingredient suggestions with alternatives, and view a generated recipe.
   *Signal:* Playwright E2E test covering the full registration → onboarding → suggestion → recipe flow passes in CI.
2. **Lab logging and trend interpretation.** A patient can log HbA1c, glucose, cholesterol, and triglyceride values and see traffic-light readings plus trend charts.
   *Signal:* Playwright test enters two consecutive lab entries and asserts the correct traffic-light state and trend direction in the UI.
3. **Diet–clinical correlation is observable.** Recommendations differ measurably between a profile with healthy labs and the same profile with elevated HbA1c.
   *Signal:* Backend integration test fixes the patient profile, varies HbA1c, and asserts that the carb-density guidance in the response changes accordingly.
4. **PWA install and native-like behaviour.** The app installs from the browser, runs full-screen with no address bar, and presents a home-screen icon and splash screen.
   *Signal:* Lighthouse PWA audit reaches the installability threshold in CI; manual install is verified on Android Chrome and iOS Safari.
5. **PHI is encrypted and access-audited.** PHI fields are encrypted at rest, all PHI endpoints require auth, and access events are written to an audit log.
   *Signal:* Pytest suite verifies that PHI columns are encrypted in the database, unauthenticated PHI requests are rejected, and an audit row is written on each PHI read.

## 8. Non-Functional Requirements

| Requirement | Target | Rationale |
|---|---|---|
| Infrastructure cost | AWS Free Tier only (RDS t3.micro, minimal compute) | Academic project budget; no recurring spend allowed |
| Deployment | Public URL with GitHub Actions CI/CD on every push to `main` | Evaluators must reach the running product without a local setup |
| HIPAA alignment | No formal certification; demonstrate encryption, RBAC, audit logs, and explicit consent | Academic scope; the practice is shown, the certification is not |
| Mobile experience | Installable PWA, mobile-first layouts, no App Store distribution | Web-stack continuity; avoids a native build pipeline within the 30-hour budget |
| Observability | Audit log for every PHI read/write (actor, action, timestamp, resource) | HIPAA-aligned practice and a reviewable signal for evaluators |
| Authentication | AWS Cognito user pool with email verification | Outsources credential storage and password policy to a managed service |
| Data retention | Documented retention policy in this product doc; PHI deletable on request | HIPAA-aligned practice and patient-consent baseline |

## 9. Constraints & Risks

| Constraint / Risk | Mitigation |
|---|---|
| 30-hour total build budget across docs, code, and deployment | Explicit scope cuts (PDF parsing, weekly meal plan, learning loop, shopping list, multi-role) recorded in §6.2 |
| PDF lab parsing complexity and format variability | Deferred to v2; replaced by a guided manual entry form covering the four canonical lab values |
| Single-developer team | Sequential delivery plan tied to the three master's milestones; no parallel tracks |
| AWS Free Tier resource limits | Architecture sized for t3.micro RDS, minimal Lambda usage, and Cognito free-tier user counts |
| AI provider variability and cost | OpenAI/Claude calls are scoped to suggestion and recipe generation; prompts and outputs are logged for the AI usage log without storing PHI in third-party logs |
| Academic timeline overlapping other coursework | Trigger-based folder growth and OpenSpec discipline prevent rework; documentation is produced once, not iterated indefinitely |

## 10. Delivery Milestones

| # | Deliverable | Date | Contents |
|---|---|---|---|
| 1 | Technical Documentation | May 27, 2026 | Product Document, User Stories, C4 Architecture, ERD |
| 2 | Functional Code | June 24, 2026 | FastAPI backend, Next.js PWA frontend, AI integration, Pytest + Playwright test suite |
| 3 | Deployed Product | July 14, 2026 | GitHub Actions CI/CD pipeline, public AWS Free Tier URL, final documentation, AI usage log |

---

## References

- `memory-bank/project-brief.md` — stakeholder brief (May 2026)
- `memory-bank/product-context.md` — competitor and patient-pain-point research
- `skills/glucochef-conventions/SKILL.md` — confirmed stack, MVP scope, security baseline, terminology, anti-patterns
- `AGENTS.md` — repository language rule, structure, and commit conventions
