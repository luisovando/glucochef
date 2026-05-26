# ADR-001 — Ship as an installable PWA instead of native iOS/Android apps

**Date:** 2026-05-25
**Status:** Accepted
**Deciders:** Luis Ovando

## Context
GlucoChef must run on the patient's phone, feel native (home-screen icon, splash, full-screen), and ship inside a 30-hour total budget that also has to cover backend, AI, tests, and CI/CD. The target audience includes patients on both iOS and Android. Building two native apps would require separate toolchains, store-review cycles, and signing infrastructure; a hybrid stack (React Native, Flutter) would still add a build pipeline that is not present in the rest of the project.

## Decision
The frontend ships as a single Next.js 14 Progressive Web App, installable from any modern mobile browser. Manifest, splash, and service worker are configured to give a native-like launch. No native or hybrid build pipeline is introduced.

## Consequences
- **Positive:** One codebase, one deploy pipeline, one URL evaluators can open without installs. Reuses the existing Next.js + TypeScript stack. Avoids App Store review for an academic deliverable.
- **Trade-off:** No access to native-only capabilities (background sync on iOS is restricted, no push on iOS Safari before 16.4, no HealthKit integration). None of these are MVP requirements.
- **Risks mitigated:** Eliminates store-submission risk for the July 14 deadline and removes the cost of maintaining two app stores from the 30-hour budget.
