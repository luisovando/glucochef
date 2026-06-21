---
name: glucochef-phase-executor
description: >
  Parametrised execution workflow for a single GlucoChef PRD phase.
  Enforces mandatory reading order, TDD Red→Green discipline for backend phases,
  Playwright assertions for frontend phases, acceptance-criteria verification,
  and do-not-change enforcement before marking any phase complete.
  Invoke with: @glucochef-phase-executor Phase {N} / {LINEAR-ID}
---

# GlucoChef Phase Executor

**Invocation pattern:** `@glucochef-phase-executor Phase {N} / {LINEAR-ID}`

**Examples:**
- `@glucochef-phase-executor Phase 0 / AI4-37`
- `@glucochef-phase-executor Phase 5 / AI4-42`
- `@glucochef-phase-executor Phase 14 / AI4-51`

---

## Phase classification

| Layer | Phases | Test discipline |
|---|---|---|
| Backend — infra & db | 0, 1, 2, 3 | Run shell ACs only |
| Backend — auth & PHI | 4, 5 | TDD Red→Green (Pytest) |
| Backend — API routes | 6–13 | TDD Red→Green (Pytest) |
| Backend — hardening | 22 | Coverage gate (`make test`) |
| Frontend — bootstrap | 14, 15 | Build + manual AC |
| Frontend — UI flows | 16–20 | Playwright assertions |
| Frontend — PWA | 21 | Lighthouse + manual |
| Frontend — E2E | 23 | Playwright headless |
| Infra — CI/CD | 24 | Dummy PR trigger |
| Infra — Deploy | 25 | Public URL smoke test |

---

## Step 0 — Mandatory reading (non-negotiable, always first)

Do not write a single line of code before completing this step.

1. Read `CLAUDE.md` — full file, every section
2. Read `docs/glucochef-prd.md § Phase {N}` — goal, dependencies, steps, ACs, do-not-change
3. Read `skills/glucochef-conventions/SKILL.md` — stack invariants and anti-patterns
4. Read `.devin/rules/tdd-red-green.md` (backend and frontend phases with test ACs)
5. **If Phase N touches PHI columns, auth, or audit log:** also read `skills/hipaa-compliance/SKILL.md`

PHI-touching phases: 3 (models placeholder), 4 (JWT), 5 (encryption + audit), 6 (onboarding), 11 (lab registration), 12 (trends).

---

## Step 1 — Verify dependencies

Before writing any code, confirm every issue listed under "Dependencies" in the PRD phase is complete.

If any dependency is not done:
- Stop immediately
- Output: `⛔ Blocked — {LINEAR-ID} depends on {DEPENDENCY-ID} which is not Done`
- Do not proceed

---

## Step 2 — Execute (discipline varies by phase layer)

### Backend phases with Pytest ACs (layers: auth/PHI, API routes, hardening)

For each acceptance criterion in the PRD phase:

**RED — Write the failing test first**
```bash
cd backend && pytest -x -v -k "{test_name}" # must FAIL here
```
Confirm the test fails before writing any implementation.
If the test passes before implementation exists, the test is wrong — fix the test.

**GREEN — Minimum implementation**
Write the minimum code that makes the test pass. No extra logic.
```bash
cd backend && pytest -x -v -k "{test_name}" # must PASS here
```

**FULL SUITE — No regressions**
```bash
cd backend && pytest -x -v
```
All previously passing tests must still pass.

Repeat RED→GREEN for each AC before moving to the next.

---

### Backend infra phases (0–3): shell acceptance criteria only

No test-first required. Execute the steps, then run each AC command verbatim.
Report the exact output.

---

### Frontend phases with Playwright ACs (16–20, 23)

1. Implement the component or route per the PRD steps
2. Write the Playwright assertion that maps to the AC
3. Run headless:
```bash
pnpm --dir frontend exec playwright test --reporter=line
```
4. Confirm the spec passes before marking the AC done

---

### Frontend bootstrap and build phases (14, 15, 21)

Run the build command from the AC after each step:
```bash
pnpm --dir frontend build   # must exit 0
```
Manual ACs (install prompt, full-screen launch) are flagged as: `⚠️ Manual verification required — {description}`

---

### Infra phases (24, 25)

Apply config and YAML changes per PRD steps.
Run the AC verification command and report the exact output.

---

## Step 3 — Verify every acceptance criterion

Run each command listed under "Acceptance Criteria" in the PRD phase.
Report each result:

```text
AC 1: {command}
→ Output: {actual output}
→ Status: ✅ PASS / ❌ FAIL / ⚠️ Manual

AC 2: ...
```

Do not proceed to Step 4 if any AC is ❌ FAIL.
Fix the issue and re-run before continuing.

---

## Step 4 — Enforce do-not-change

Run:
```bash
git diff --name-only
```

Cross-check the output against the "Do not change" list in the PRD phase.

**Global do-not-change (every phase):**
- `AGENTS.md`
- `CLAUDE.md`
- `README.md`
- `memory-bank/**` (except `decisions.md` and `ai-usage-notes.md` — append-only)
- `skills/**`
- `.windsurf/skills/**`
- `docs/product-doc.md`
- `docs/glucochef-prd.md`

If any protected file appears in `git diff --name-only`:
- Revert it: `git checkout HEAD -- {file}`
- Report the violation: `⛔ Protected file modified and reverted: {file}`

---

## Step 5 — Output report and propose git artifacts

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Phase {N} — {LINEAR-ID} — {GOAL}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Acceptance Criteria:
  ✅ AC 1: {description}
  ✅ AC 2: {description}
  ⚠️  AC 3: {description} — manual verification required

Protected files: no violations

Branch:  feat/{linear-id-lowercase}-phase-{n}-{slug}
Commit:  feat({LINEAR-ID}): phase {N} — {goal one-liner}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Branch naming example for AI4-37:
`feat/ai4-37-phase-0-repository-scaffolding`

---

## Hard anti-patterns — never do these

- **Do not skip Step 0.** Context in the window is never sufficient to bypass reading order.
- **Do not write implementation before seeing a failing test** (backend phases with Pytest ACs).
- **Do not mark an AC done without running its command.** Assumed passes are not passes.
- **Do not modify any file in the do-not-change list.** Revert immediately if it happens.
- **Do not create OpenSpecs, ADRs, or new docs unless the PRD step explicitly requires it.** The PRD is the spec.
- **Do not add features, helpers, or abstractions not listed in the phase steps.** Out-of-scope additions are rejected even if "cleaner".
- **Do not start the next phase** until Step 5 is complete and all ACs are ✅ or ⚠️ (manual).
- **Do not pad test assertions.** `assert True` is not a test.
