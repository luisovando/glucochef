# ADR-002 — Encrypt PHI at the field level with AES-256-GCM

**Date:** 2026-05-25
**Status:** Accepted
**Deciders:** Luis Ovando

## Context
The product handles Protected Health Information: diagnosis, medications, allergies, intolerances, rejected foods, and lab values (HbA1c, glucose, cholesterol, triglycerides). The security baseline in `skills/glucochef-conventions/SKILL.md` requires PHI to be encrypted at rest and access to be auditable. AWS RDS offers volume-level encryption out of the box, but a leaked database dump or a misconfigured read replica would still expose PHI in plaintext to anyone holding the dump file. The MVP also has to demonstrate a HIPAA-aligned practice for academic evaluation, not merely "the disk is encrypted".

## Decision
PHI columns are encrypted at the field level with AES-256-GCM through `PHI Crypto Service` before they reach PostgreSQL. The encryption key is sourced from AWS KMS at process start, never persisted in application code, and never reaches the PWA. Volume-level RDS encryption stays on as a second layer. The only path to PHI columns is through FastAPI services, which always pair decryption with a row in `Audit Log Service`.

## Consequences
- **Positive:** A leaked database dump exposes ciphertext only. PHI can be reasoned about as a single, narrow surface (`PHI Crypto Service` + audit). Maps cleanly onto user story `US-01-SEC` ("Raw database rows for PHI fields are ciphertext").
- **Trade-off:** Encrypted columns cannot be queried with SQL `LIKE`, ordered, or indexed on plaintext. The MVP does not require any such query (lab trends fetch the last N rows by `created_at`; suggestions and recipes operate on decrypted in-memory objects). Any future feature that needs server-side filtering on PHI must revisit this ADR.
- **Risks mitigated:** Reduces the blast radius of a database compromise and of a misconfigured backup to the loss of a KMS-protected key, which is governed independently.
