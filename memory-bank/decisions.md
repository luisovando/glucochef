# Decisions log

Append-only record of decisions that deviate from a stated default, resolve an ambiguity, or codify a non-obvious trade-off. New entries go at the bottom. Each entry is dated, scoped, and justified. Once written, entries are not edited — superseding decisions are added as new entries that reference the old one.

Format:

```
## YYYY-MM-DD — <short title>
**Scope:** <area touched>
**Status:** accepted | superseded by <entry> | reversed
**Context:** what forced the decision
**Decision:** what we chose
**Rationale:** why this option over alternatives
**Consequences:** what now follows from this
```

---

## 2026-05-25 — Data model has 12 tables, not the 7 mentioned in PRD phase 3

**Scope:** Data model (`docs/erd.md`), Alembic phase 3 migration.
**Status:** accepted.
**Context:** PRD phase 3 enumerates seven entities (`Patient`, `NutritionalProfile`, `RejectedIngredient`, `LabResult`, `Suggestion`, `Recipe`, `AuditLogEntry`). `skills/glucochef-data/SKILL.md` requires 3NF: multi-valued attributes (medications, allergies, intolerances, dietary preferences) must live in child entities, and a list of AI suggestion alternatives must be its own entity.
**Decision:** Ship the MVP with twelve tables: `patients`, `nutritional_profiles`, `medications`, `allergies`, `intolerances`, `dietary_preferences`, `rejected_ingredients`, `lab_results`, `suggestions`, `suggestion_alternatives`, `recipes`, `audit_log_entries`.
**Rationale:** Storing multi-valued PHI as comma-separated strings or JSON arrays inside a parent table is explicitly listed as an anti-pattern in the data skill. The PRD's table count is approximate; its acceptance criterion ("all tables with correct foreign keys") still holds at twelve tables.
**Consequences:** The phase 3 Alembic migration creates twelve tables plus four ENUM types. Tests that assert table count must use the twelve-table list, not the PRD's count.

---

## 2026-05-25 — JSONB for `recipes.content` and `*_clinical_context_summary` columns

**Scope:** Physical schema (`recipes`, `suggestions`).
**Status:** accepted.
**Context:** The data skill restricts JSONB to "immutable AI-generated artifacts" and forbids storing numeric PHI inside JSONB. The MVP needs to persist (a) generated recipes — title, ingredient list, steps, nutrition summary — and (b) the clinical context attached to each suggestion or recipe at generation time, so the AI usage log and audit trail remain reproducible.
**Decision:**
- `recipes.content JSONB NOT NULL` stores the full AI-generated recipe payload as a single immutable JSON document.
- `suggestions.clinical_context_summary JSONB` and `recipes.clinical_context_summary JSONB` store **only derived traffic-light status strings** (e.g., `{"hba1c":"red","triglycerides":"amber"}`).
**Rationale:** A recipe is the canonical example of an immutable AI artifact: produced once, never patched in place, retrieved as a whole. Normalizing it into `recipe_ingredients`, `recipe_steps`, and `recipe_nutrition` tables would add three tables and zero query value for the MVP read pattern (`GET /recipes/{id}` returns everything). For the context summaries, storing derived status strings — not raw values — sidesteps the "numeric PHI in JSONB" anti-pattern while still letting the AI provider and audit log reconstruct what clinical state shaped each output.
**Consequences:**
- `recipes.content` is treated as PHI-by-association at the access-control and audit layers; it is served only through audited endpoints and is never re-sent to the AI provider as input.
- Any code path that writes to a `clinical_context_summary` column must pass through `app/services/labs.py::evaluate` and persist only `green|amber|red` strings. Adding numeric values to those JSONB blobs is a review-blocker.
- If a future feature requires querying inside `recipes.content` (e.g., "find recipes containing X"), revisit this decision rather than adding GIN indexes ad hoc.

---

## 2026-05-25 — `audit_log_entries.patient_id` is nullable and has no cascade

**Scope:** Audit log schema, right-to-erasure procedure.
**Status:** accepted.
**Context:** The data skill states the audit log is exempt from right-to-erasure: forensic rows must outlive the patient. PostgreSQL's default FK behaviour would either block patient deletion or cascade-delete the audit trail.
**Decision:** `audit_log_entries.patient_id UUID NULL REFERENCES patients(id)` — no `ON DELETE CASCADE`, no `ON DELETE SET NULL`. The right-to-erasure procedure soft-deletes patients (`deleted_at`), which leaves the audit FK intact. If external compliance ever requires a hard delete of the `patients` row, the operator nulls the FK on the affected audit rows manually rather than removing them.
**Rationale:** Cascade deletion would destroy the forensic record; a hard `NOT NULL` would block legitimate erasure flows. A nullable FK with no automatic action is the only option that preserves both properties.
**Consequences:** Application code that joins audit rows back to a patient must handle `patient_id IS NULL`. Queries that count audit events per active patient should filter on `patients.deleted_at IS NULL` explicitly.

---

## 2026-05-25 — `dietary_preferences.preference` is not PHI

**Scope:** PHI classification, encryption surface.
**Status:** accepted.
**Context:** Medications, allergies, intolerances, and rejected ingredients are PHI because they reveal a clinical condition. Cultural or dietary preferences (`mediterranean`, `low-sodium`, `vegetarian`, `kosher`, etc.) sit closer to lifestyle data than to clinical data.
**Decision:** `dietary_preferences.preference VARCHAR(80)` is stored as plaintext, with a DB-level `UNIQUE (nutritional_profile_id, preference)` constraint. It is not wrapped in `EncryptedString`.
**Rationale:** A preference tag on its own does not indicate a diagnosis; encrypting it would block useful uniqueness and lookup behaviour at the database layer without a meaningful privacy gain.
**Consequences:** If a future requirement allows free-text preference notes that could leak clinical information (e.g., "avoids gluten because celiac"), this column must move to `EncryptedString` and a new entry must supersede this one.
