# ADR-003 — Capture lab values through a guided manual form; defer PDF parsing to v2

**Date:** 2026-05-25
**Status:** Accepted
**Deciders:** Luis Ovando

## Context
Patients receive lab results as PDFs from heterogeneous laboratories with no standard layout. Automating ingestion would require either OCR + per-lab templates or a generalist parsing model with an evaluation harness, both of which carry unbounded edge-case work. The MVP needs reliable structured access to four canonical metrics — HbA1c, fasting glucose, total cholesterol, triglycerides — to power the traffic-light view and the diet-clinical correlation. The 30-hour budget cannot absorb the parsing-quality long tail without sacrificing core scope.

## Decision
Lab capture in the MVP is a guided manual form that validates each value against a known clinical range before submission. The PDF parser is modelled in `glucochef.c4` as `#deferred` so reviewers can see the v2 surface, but it is excluded from every MVP view and is not implemented.

## Consequences
- **Positive:** Removes parsing risk from the critical path. The four canonical metrics are always present and well-typed, so `Lab Service`, `Correlation Policy`, and the trend computation operate on clean inputs. Inline validation (`US-02-LAB`) gives the patient immediate feedback and protects the trend chart from typos.
- **Trade-off:** The patient has to type four values per visit. For a quarterly lab cadence this is acceptable.
- **Risks mitigated:** Avoids spending budget on edge cases (rotated PDFs, scanned images, non-Latin lab reports) that would not improve clinical value within the academic timeline.
