# How is the nutritional profile created with explicit consent?

Covers `US-04-ONB` and `US-03-SEC`. Submitting onboarding without consent is rejected; submitting with consent persists the profile and writes an audit row.

```mermaid
sequenceDiagram
    actor Patient
    participant PWA as PWA Frontend
    participant API as Backend API
    participant Profile as Profile Service
    participant Crypto as PHI Crypto Service
    participant Audit as Audit Log Service
    participant DB as PostgreSQL

    Patient->>PWA: Complete onboarding steps + check consent
    PWA->>API: POST /profile (JWT bearer, profile + consent=true)
    API->>API: Auth Adapter verifies JWT
    API->>Profile: Create or update profile
    Profile->>Crypto: Encrypt PHI fields (allergies, intolerances, rejections, diagnosis)
    Crypto-->>Profile: Ciphertext payload
    Profile->>DB: UPSERT nutritional_profile
    Profile->>Audit: Log "profile.upsert" + "consent.granted"
    Audit->>DB: INSERT audit_log row
    Profile-->>API: Profile id
    API-->>PWA: 201 Created
    PWA-->>Patient: Redirect to suggestions
```
