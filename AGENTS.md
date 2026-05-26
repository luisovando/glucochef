# GlucoChef

GlucoChef is a smart nutritional assistant for patients managing diabetes. The product delivers personalized meal planning with dynamic ingredient alternatives (based on allergies, intolerances, and preferences) and manual lab result tracking with a traffic-light interpretation system. It is shipped as a mobile-first Progressive Web App.

This document is the entry point for any AI agent or human contributor working in this repository. Read it first, then follow the pointers below to the relevant context for your task.

## Project context

GlucoChef is the capstone project for a master's program. Three deliverables structure the timeline:

| Date | Deliverable |
|---|---|
| May 27, 2026 | Technical documentation (Product Doc, User Stories, C4 Architecture, ERD) |
| June 24, 2026 | Functional code (backend, frontend, AI integration, test suite) |
| July 14, 2026 | Deployed product (CI/CD pipeline, public URL, final docs, AI usage log) |

Total work budget: approximately 30 hours. Any proposal that does not fit this budget must be challenged or deferred. Scope discipline matters more than feature volume.

## Language

All content in this repository is written in English: documentation, code, identifiers, comments, commit messages, skill files, OpenSpec specs, and root-level files. No artifact stored in this repo is written in any other language. User-facing UI copy targeted at Spanish-speaking patients is the only exception and is handled through the i18n layer of the frontend, not by changing the source language of the repo.

## Repository structure

```
glucochef/
├── AGENTS.md            ← you are here: universal entry point
├── CLAUDE.md            ← Claude-specific behavior on top of this file
├── README.md            ← human-facing project overview
├── memory-bank/         ← persistent project context (brief, research, decisions)
├── skills/              ← reusable conventions for producing artifacts
├── docs/                ← formal deliverables for the master's program
├── openspec/            ← spec-driven changes (proposal → specs → design → tasks)
├── backend/             ← FastAPI service
└── frontend/            ← Next.js PWA
```

The structure grows by trigger, not all at once. A folder appears in the repo only when there is real content for it. Empty scaffolding is avoided.

## Where to look for what

| If you need... | Read... |
|---|---|
| Product principles, MVP scope, terminology, anti-patterns | `skills/glucochef-conventions/SKILL.md` |
| Original brief and prior research | `memory-bank/project-brief.md`, `memory-bank/product-context.md` |
| How to write a specific artifact type | `skills/glucochef-<artifact>/SKILL.md` |
| What change is currently being worked on | `openspec/changes/` |
| Architectural decisions and patterns | `memory-bank/system-patterns.md`, `memory-bank/decisions.md` |
| Master deliverables (Product Doc, US, C4, ERD) | `docs/` |

## How to work in this repo

1. **Read `skills/glucochef-conventions/SKILL.md` before producing any artifact.** It defines the stack, scope, product principles, security baseline, terminology, and anti-patterns. Aligning with it is mandatory.
2. **When a relevant skill exists for the task, use it.** Skills are reusable rules for specific artifact types (product doc, user stories, architecture, ERD). Do not reinvent conventions when one already exists.
3. **For non-trivial features, use OpenSpec.** Create a change folder under `openspec/changes/` with proposal, specs, design, and tasks before writing code. Small fixes, copy tweaks, or one-line corrections do not require this ceremony.
4. **Maintain the AI usage log incrementally.** Notes about prompts, decisions, and AI-assisted outputs are captured in `memory-bank/ai-usage-notes.md` as work happens, and curated into `docs/ai-usage-log.md` for the final delivery. Reconstructing this log from memory at the end is not viable.

## Tech stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python) |
| Frontend | Next.js 14 as a Progressive Web App |
| Database | PostgreSQL on AWS RDS |
| Authentication | AWS Cognito |
| AI | OpenAI / Claude API |
| CI/CD | GitHub Actions → AWS Free Tier |
| Testing | Pytest (backend), Playwright (frontend) |

Stack rationale, security posture, and HIPAA-aligned design notes live in `skills/glucochef-conventions/SKILL.md`. Deviations from this stack require explicit justification in `memory-bank/decisions.md`.

## Scope boundary

The MVP scope is fixed and documented in `skills/glucochef-conventions/SKILL.md`. Features deferred to v2 — PDF lab parsing, full weekly meal planning, intelligent feedback loop, shopping list, multi-user roles — must not be implemented in this iteration, even if technically feasible. If unsure whether a feature is in scope, consult the conventions skill before proceeding.

## Commit and PR conventions

- Conventional Commits style: `<type>(<scope>): <subject>` (e.g., `feat(onboarding): add allergy intake step`)
- One logical change per commit when possible
- PR descriptions reference the relevant OpenSpec change folder when applicable
- Commits and PRs are written in English, consistent with the rest of the repo