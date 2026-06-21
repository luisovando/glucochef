# Product Context for GlucoChef

> Source: prior research conducted for the GlucoChef proposal (May 2026). This file is the English markdown rendering of that research, kept editable as project context. The original PDF is preserved separately.

## 1. Competitor landscape

The main diabetes-management apps surveyed:

**mySugr** (Roche, 4+ million users). Focused on glucose tracking with Accu-Chek devices. Includes a bolus calculator, estimated HbA1c, motivational challenges, and a gamified "monster" mascot. Main limitations: very narrow integration (Accu-Chek only), no data sharing across devices, and extremely basic nutrition (just meal photos in the Pro version). Does not track lab results and does not offer meal plans.

**Glucose Buddy** (Azumio, ~30K users). Integrates with Dexcom and Fitbit. Its "Meal IQ" feature uses AI to learn how certain foods affect the user's glucose. Problems: very high price (up to $59.99/month), heavy ads in the free tier, frequent bugs, non-existent customer support, and no lab tracking either.

**Klinio.** Focused on meal plans and recipes for type 2 diabetes. Studies show that frequent use reduces HbA1c. But it is generic; it does not personalize against the patient's lab values.

**CGM apps** (Dexcom, LibreLink). Display only real-time glucose data. They do not connect with nutrition or lab tracking.

## 2. Real patient pain points (from Reddit communities)

From threads in r/diabetes and r/diabetes_t2, the following recurring patterns emerged:

**On food.** The top frustration is the constant complexity of thinking about everything they eat. Patients report that rice and hidden carbohydrates are a constant pain. Nutritional advice is contradictory across forums, doctors, and apps. They struggle to maintain a sustainable diet (total restriction does not work).

**On daily management.** The hardest part is that literally anything can affect glucose (stress, illness, sleep, exercise). The mental and emotional weight ("diabetes burnout") is enormous, with associated shame and depression.

**On existing apps.** Patients complain about having to use multiple apps (one for glucose, another for food, another for exercise). Manual data entry is tedious. There is a lack of real personalization based on the patient's specific condition.

## 3. The gap GlucoChef can cover

After analyzing competitors and pain points, a clear market gap was identified:

> No app integrates in a single place: personalized nutrition for diabetic patients + lab tracking + correlation between what you eat and how your clinical indicators evolve.

Existing apps split into two worlds that do not talk to each other:

- Real-time glucose trackers (mySugr, Glucose Buddy)
- Generic recipe suggesters (Klinio)

None of them cross lab data (HbA1c, fasting glucose, cholesterol, triglycerides, creatinine) with the patient's diet to surface correlations and trends.

## 4. HIPAA considerations for the MVP

Based on the research, the minimum needed to demonstrate HIPAA understanding for this project (without requiring formal certification, but showing the practice is understood) includes:

- Encryption of data at rest (AES-256 for PHI fields in the database) and in transit (TLS 1.2+)
- Role-based access control (RBAC)
- Audit logs for access to health data
- Explicit user consent to store PHI
- Documented data retention policy

This can be implemented as middleware in the backend and documents excellently in the architecture.

## 5. Research methodology used (4 layers)

The research followed a four-layer structure that future iterations can deepen:

**Layer 1 — Competitor analysis.** Download and test mySugr, Glucose Buddy, and Klinio. Build a feature comparison table. Identify gaps.

**Layer 2 — Voice of the user.** Read threads on Reddit (r/diabetes, r/diabetes_t2), reviews on App Store and Google Play for existing apps. Look for repeating complaint patterns.

**Layer 3 — Clinical validation.** Review articles in PubMed/JMIR on the effectiveness of diabetes apps (several found, including a JMIR Diabetes 2025 study that analyzes 602 user reviews and categorizes 11 feature types). This provides academic backing.

**Layer 4 — Technical feasibility.** Validate that the chosen stack (FastAPI + PostgreSQL + Next.js) can handle PHI encryption, audit logging, and CI/CD deployment within the available time.