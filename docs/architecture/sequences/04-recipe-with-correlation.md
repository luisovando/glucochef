# How does a red HbA1c tighten the next recipe?

Covers `US-01-RCP`, `US-02-RCP`, and `US-01-COR`. The recipe service consults `Correlation Policy`, which reads the latest traffic-light state from `Lab Service` and decides whether the carb-restricted policy applies.

```mermaid
sequenceDiagram
    actor Patient
    participant PWA as PWA Frontend
    participant API as Backend API
    participant Recipe as Recipe Service
    participant Profile as Profile Service
    participant Corr as Correlation Policy
    participant Lab as Lab Service
    participant AI as AI Provider
    participant DB as PostgreSQL
    participant Audit as Audit Log Service

    Patient->>PWA: Tap "Generate Recipe"
    PWA->>API: POST /recipes (accepted ingredients)
    API->>Recipe: Generate from accepted ingredients
    Recipe->>Profile: Read preferences + accepted ingredients
    Recipe->>Corr: Resolve carb policy
    Corr->>Lab: Latest traffic-light state
    Lab-->>Corr: HbA1c = red
    Corr-->>Recipe: Policy = carb-restricted (<= 45 g/serving)
    Recipe->>AI: Prompt with ingredients + policy
    AI-->>Recipe: Recipe draft
    Recipe->>Recipe: Apply carb-restricted badge + cap
    Recipe->>DB: Persist recipe
    Recipe->>Audit: Log "recipe.generated"
    Recipe-->>API: Recipe payload
    API-->>PWA: 201 Created
    PWA-->>Patient: Recipe page (title, ingredients, steps, nutrition + carb-restricted badge)
```
