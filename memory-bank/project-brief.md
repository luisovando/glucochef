# Project Brief for GlucoChef

> Source: stakeholder brief delivered May 2026 for the master's capstone project. This file is the English markdown rendering of that brief, kept editable as project context. The original PDF is preserved separately.

**Status:** Draft for validation
**From:** Stakeholder / Client
**To:** Chief Product Officer
**Date:** May 2026

## Context

Patients with diabetes face a daily problem that technology has not solved well: they do not know what to eat. Generic nutritional guides exist, but they speak to a population, not to the individual. They tell the patient "eat salmon" without asking whether they like it, are allergic to it, or can afford it. The result is dietary abandonment.

In parallel, lab studies (HbA1c, glucose, lipid profile) arrive every three to six months as a PDF the patient does not understand. The numbers do not connect to concrete actions: if my HbA1c went up, what should I change about how I eat?

## Problem

1. **Diet for the diabetic patient is not personalized.** Existing apps offer static "for diabetics" recipe catalogs that do not consider individual preferences, allergies, or taste.
2. **Lab results are disconnected from action.** The patient receives numbers they cannot interpret and that do not translate into concrete changes in their daily life.
3. **There is no feedback loop between food and clinical evolution.** Diet and labs live in separate worlds.

## Expected product

A mobile-first Progressive Web App named **GlucoChef** — a smart nutritional assistant that:

- **Knows the patient:** diabetes type, medication, allergies, intolerances, disliked foods, cultural and dietary preferences.
- **Suggests with alternatives:** instead of saying "eat salmon", offers 3-4 nutritionally equivalent options (trout, sardines, chia, walnuts) respecting the patient's restrictions. If the patient rejects an option, it is not suggested again.
- **Generates personalized recipes:** built from the ingredients the patient accepted, not from a fixed catalog.
- **Interprets labs:** the patient logs their values and the app displays them with a traffic-light system (green/amber/red) in plain language, explaining what each result means.
- **Connects diet to clinical reality:** if HbA1c goes up, nutritional recommendations adjust automatically.

## Target users

**Primary:** adult patients with type 1, type 2, or gestational diabetes who want to improve their diet and understand their lab results.

**Secondary (future):** nutritionists and physicians who want to remotely follow their patients' diet and clinical values.

## MVP scope

### Included

- Complete nutritional onboarding — medical profile, allergies, intolerances, rejected foods, preferences
- Suggestion engine with alternatives — ingredient recommendations with equivalent substitutes, AI-powered
- On-demand recipe generation — recipes built from ingredients accepted by the patient, not a static catalog
- Lab tracking with smart visualization — guided manual entry of common studies (HbA1c, glucose, cholesterol, triglycerides), with trend charts and traffic-light visualization
- Diet-lab connection — clinical values feed back into nutritional recommendations
- HIPAA-aligned design — encryption of sensitive data, access auditing, secure authentication. Formal certification is not pursued, but health-data protection practices are demonstrated.
- Mobile (PWA) experience — installable from the browser, full-screen with no browser bar, home-screen icon, splash screen

### Deferred to v2

- **Lab PDF upload** — automatic value extraction from the lab document. Deferred because lab formats vary significantly and technical risk is high for the current timeline.
- **Full 7-day weekly meal plan** — multi-day nutritional balancing. The MVP generates individual recipes.
- **Intelligent feedback loop** — the system learning from rejections and patient ratings to improve future recommendations. In MVP, rejection simply filters the ingredient.
- **Shopping list** — generated from chosen recipes. Low effort; included if time allows.
- **Multi-user with roles** — nutritionist/physician view with access to assigned patients.

## Constraints

- **Infrastructure budget:** cloud free tier.
- **Regulatory:** no formal HIPAA certification required, but the design must demonstrate the fundamental practices (encryption, auditing, access control).

## Expected deliveries

| # | Delivery | Date | Contents |
|---|---|---|---|
| 1 | Technical documentation | May 27, 2026 | Product Doc, User Stories, Architecture, Data Model |
| 2 | Functional code | June 24, 2026 | Backend, frontend, AI integration, test suite |
| 3 | Deployed product | July 14, 2026 | CI/CD pipeline, public URL, final documentation, AI usage log |

## Success criteria

1. A patient can register, configure their profile, receive food suggestions with alternatives, and see recipes generated from their choices.
2. A patient can log lab values and see their trends with clear visual interpretation.
3. Nutritional recommendations reflect both the patient's profile and their clinical values.
4. The app installs from the browser and is used from the phone with a native-app experience (PWA), without going through an app store.
5. Health data is protected with encryption and access auditing.