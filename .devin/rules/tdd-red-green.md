---
trigger: model_decision
---

**Scope**: Backend phases with Pytest ACs (Phases 4–13, 22) and frontend phases
with Playwright ACs (Phases 16–20, 23).

**Exceptions — shell ACs only, no TDD cycle required**:

Phases 0–3 (scaffolding, bootstrap, DB, models): verify with shell commands only
Phases 14, 15, 21 (frontend bootstrap, Cognito UI, PWA): verify with build commands and manual checks
Phases 24–25 (CI, deploy): verify with pipeline triggers and URL smoke tests

---

## Mandatory cycle — one AC at a time

### 🔴 RED — Test first

1. Read the acceptance criterion from the Linear issue or PRD phase
2. Write the test that asserts that criterion — nothing else
3. Run the test and **confirm it fails**:
   ```bash
   cd backend && pytest -x -v -k "{test_name}"
   # Expected: FAILED — if it passes, the test is wrong
   ```
4. Do not write a single line of implementation until the test is red

### 🟢 GREEN — Minimum implementation

5. Write the minimum code that makes the failing test pass
6. Run the test and **confirm it passes**:
   ```bash
   cd backend && pytest -x -v -k "{test_name}"
   # Expected: PASSED
   ```
7. Do not add logic not required by the current failing test

### ✅ NO REGRESSIONS

8. Run the full suite:
   ```bash
   cd backend && pytest -x -v
   ```
9. All previously passing tests must still pass
10. Only then move to the next acceptance criterion

---

## Frontend Playwright variant

For frontend ACs with Playwright assertions:

1. Implement the component or route
2. Write the Playwright assertion that maps to the AC
3. Run headless and confirm it passes:
   ```bash
   pnpm --dir frontend exec playwright test --reporter=line
   ```

---

## Hard rules

| Rule | Rationale |
|---|---|
| Never skip RED | A test that was never red gives false confidence |
| Never pad assertions | `assert True` or `expect(true).toBe(true)` is not a test |
| One AC per cycle | Do not batch multiple ACs into one RED→GREEN loop |
| No implementation before RED | Not negotiable, even for "obvious" code |
| Report the failing output | Paste the actual pytest/playwright output in the RED step |

---

## Quick reference

```bash
# Run a single test by name (backend)
cd backend && pytest -x -v -k "test_name"

# Run all tests, stop on first failure
cd backend && pytest -x -v

# Run full suite with coverage (Phase 22+)
cd backend && make test

# Run Playwright headless (frontend)
pnpm --dir frontend exec playwright test --reporter=line

# Run a single Playwright spec
pnpm --dir frontend exec playwright test tests/onboarding.spec.ts
```
