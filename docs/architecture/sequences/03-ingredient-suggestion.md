# How are allergy- and rejection-aware alternatives produced?

Covers `US-01-SUG` through `US-04-SUG`. The AI provider proposes candidates; the backend filters allergens and persisted rejections before returning a list to the patient. The system fails loudly when fewer than three valid alternatives remain.

```mermaid
sequenceDiagram
    actor Patient
    participant PWA as PWA Frontend
    participant API as Backend API
    participant Suggest as Suggestion Service
    participant Profile as Profile Service
    participant Lab as Lab Service
    participant Corr as Correlation Policy
    participant AI as AI Provider
    participant Audit as Audit Log Service

    Patient->>PWA: Request alternatives for "salmón"
    PWA->>API: POST /suggestions (ingredient="salmón")
    API->>Suggest: Build request
    Suggest->>Profile: Read allergies + rejections
    Suggest->>Lab: Read latest traffic-light state
    Suggest->>Corr: Resolve constraints from latest labs
    Corr-->>Suggest: Carb policy (baseline | restricted)
    Suggest->>AI: Prompt with de-identified profile + policy
    AI-->>Suggest: Candidate alternatives
    Suggest->>Suggest: Filter allergens + rejections + duplicates
    alt 3-4 valid alternatives
        Suggest->>Audit: Log "suggestion.served"
        Suggest-->>API: Alternatives
        API-->>PWA: 200 OK
        PWA-->>Patient: Show 3-4 alternatives
    else fewer than 3 valid
        Suggest->>Audit: Log "suggestion.insufficient"
        Suggest-->>API: 422 Unprocessable
        API-->>PWA: 422
        PWA-->>Patient: "Try again" error (no padding)
    end
```
