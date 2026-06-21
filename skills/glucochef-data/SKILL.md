---
name: glucochef-data
description: >
  Conventions and rules for authoring the GlucoChef data model. Use whenever
  producing or updating the ERD, SQLAlchemy models, Alembic migrations, or any
  schema decision. Triggers on: ERD, data model, schema, migration, entity,
  table, PHI column, foreign key, index, EncryptedString, or any named entity
  in the GlucoChef domain. Also triggers on PRD Phase 3 and Phase 5.
---

# GlucoChef — Data Model Conventions

## Output locations

| Artifact | Path |
|---|---|
| ERD (all three model levels) | `docs/erd.md` |
| SQLAlchemy models | `backend/app/models/` |
| Alembic migrations | `backend/alembic/versions/` |
| Custom ENUM definitions | `backend/app/models/enums.py` |
| Clinical thresholds | `backend/app/services/` (constants, not schema) |

---

## Three-level modelling sequence

Produce `docs/erd.md` in exactly this order. Each level builds on the previous one.

### Level 1 — Conceptual model
Business-facing. Answers: *what* needs to be stored and how concepts relate.

- List entities as business concepts only — no attributes, no types, no column names.
- Show relationships in plain language (e.g. "a patient logs many lab results").
- Audience: stakeholder or product reviewer with no SQL knowledge.
- Format: Mermaid `erDiagram` with empty entity blocks and labeled relationship lines only.

### Level 2 — Logical model
Technology-agnostic. Answers: *how* data is structured, with attributes and normalization applied.

- Add attributes with logical types (`string`, `decimal`, `date`, `boolean`, `text`).
- Apply 3NF: every non-key attribute depends on the whole key and nothing but the key. Split multi-valued attributes (lists of medications, allergies, intolerances, preferences) into child entities.
- Specify cardinality and whether relationships are mandatory or optional.
- Mark PHI entities and attributes with `⚠ PHI`. Do not reference encryption mechanisms yet.
- No database-specific types, no indexes, no constraint syntax.
- Format: Mermaid `erDiagram` with logical-type columns.

### Level 3 — Physical model
PostgreSQL-specific. Answers: *how to implement* the logical model in the target database.

- Map every logical type to a concrete PostgreSQL type.
- Apply PHI encryption: PHI columns become `TEXT` (Fernet ciphertext); note the logical type in a quoted ERD comment.
- Add surrogate PKs as `UUID DEFAULT gen_random_uuid()`.
- Add `created_at TIMESTAMPTZ NOT NULL DEFAULT now()` to every table; add `updated_at` only on mutable tables.
- Add `deleted_at TIMESTAMPTZ` to the patient root table for right-to-erasure support.
- Use `DATE` for clinical sample dates, `TIMESTAMPTZ` for system events.
- Specify UNIQUE, CHECK, and FK constraints with ON DELETE behaviour.
- Define required indexes (see index requirements section below).
- JSONB only for immutable AI-generated artifacts; document any use in `memory-bank/decisions.md`.
- Format: Mermaid `erDiagram` with physical-type columns, followed by the entity catalogue prose.

---

## PHI rules

### What counts as PHI
Any attribute that contains or implies a health condition linked to an identifiable patient: lab values, medications, allergies, intolerances, and food rejections (which can reveal allergies or intolerances). Email is not stored in this database — it lives in AWS Cognito.

### How to handle PHI columns (Level 3 only)
- Implement as `EncryptedString` (Fernet ciphertext stored as `TEXT`).
- Mark with `⚠ PHI` in the ERD comment.
- Never add a DB-level `UNIQUE` constraint on an encrypted column — enforce uniqueness in the repository layer after decryption.
- Never write PHI to application logs or AI provider prompts.

### Right to erasure
- The patient root table must have `deleted_at TIMESTAMPTZ` (soft-delete).
- On a deletion request: hard-delete all child PHI rows first, then set `deleted_at`.
- The audit log table is exempt — its rows are forensic records that must outlive the patient. Its FK to the patient table has no `ON DELETE CASCADE`.

### PHI-adjacent data
IP addresses in the audit log are linked to health record access events: store only in the audit table under access control, never in application logs, never exposed via a public API endpoint.

---

## ERD format

The ERD in `docs/erd.md` contains three clearly separated sections — one per level — each with a Mermaid `erDiagram` block. Level 3 is followed by a prose entity catalogue with one section per table (columns, constraints, indexes, notes).

PHI comment notation in Level 3 columns:
```
TEXT column_name "⚠ PHI · EncryptedString · logical: <type>"
```

---

## Index requirements

Every table must cover at minimum:
- Its most frequent lookup predicate (typically the FK used in `WHERE` clauses).
- Any column used in `ORDER BY` for paginated or trend queries.
- Never index encrypted columns — ciphertext indexes are meaningless.

---

## Alembic conventions

- One migration per PRD phase.
- Every migration implements a reversible `downgrade()`.
- Never embed plaintext PHI in seed data or migration comments.
- Run `alembic check` in CI to detect model/migration drift.

---

## Anti-patterns

- Multi-valued facts stored as comma-separated strings or JSON arrays in a parent table → child entity.
- `UNIQUE` on an encrypted column at DB level → repository layer.
- Numeric PHI values in snapshot or context JSONB fields → store derived status strings only (e.g. `green|amber|red`).
- `ON DELETE CASCADE` on the audit log FK → forensic rows outlive the patient.
- Hard-deleting a patient without first erasing child PHI → follow right-to-erasure order.
- Clinical thresholds as schema values → service-layer constants only.
- IP addresses in application logs → audit table only.
- Skipping Level 1 or Level 2 and writing the physical model directly → always produce all three levels in sequence.