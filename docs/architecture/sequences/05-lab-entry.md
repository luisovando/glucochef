# How is a lab entry stored, interpreted, and audited?

Covers `US-01-LAB` through `US-04-LAB`, plus `US-01-SEC` and `US-04-SEC`. Values are validated, encrypted at the field level, persisted, and surfaced as traffic-light cards with a trend computed from the latest three entries.

```mermaid
sequenceDiagram
    actor Patient
    participant PWA as PWA Frontend
    participant API as Backend API
    participant Lab as Lab Service
    participant Crypto as PHI Crypto Service
    participant DB as PostgreSQL
    participant Audit as Audit Log Service

    Patient->>PWA: Submit lab entry (HbA1c, glucose, cholesterol, triglycerides, date)
    PWA->>API: POST /labs (JWT bearer)
    API->>Lab: Validate ranges
    alt Out of range
        Lab-->>API: 422 with field errors
        API-->>PWA: 422
        PWA-->>Patient: Inline validation errors
    else Valid
        Lab->>Crypto: Encrypt PHI fields
        Crypto-->>Lab: Ciphertext
        Lab->>DB: INSERT lab_entry
        Lab->>Audit: Log "labs.write"
        Lab-->>API: Entry id
        API-->>PWA: 201 Created
    end

    Patient->>PWA: Open lab trends
    PWA->>API: GET /labs/trends
    API->>Lab: Compute traffic-light + trend
    Lab->>DB: SELECT last N lab_entry rows
    Lab->>Crypto: Decrypt PHI fields
    Lab->>Lab: Map values to green/amber/red + direction
    Lab->>Audit: Log "labs.read"
    Lab-->>API: Cards + trend
    API-->>PWA: 200 OK
    PWA-->>Patient: Traffic-light cards (trend hidden if entries < 3)
```
