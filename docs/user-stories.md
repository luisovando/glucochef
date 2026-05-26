# User Stories

**Version:** 1.0 (MVP)
**Date:** May 2026
**Audience:** Technical academic evaluators, AI coding agents
**Status:** Baseline for Delivery 1 (Technical Documentation, May 27, 2026)

**Source of truth:** `docs/product-doc.md` (scope, personas) and `docs/glucochef-prd.md` (phase acceptance criteria).
**Authoring rules:** `skills/glucochef-user-stories/SKILL.md`.

All stories follow the canonical persona `Patient` (adult 18+ with Type 1, Type 2, or gestational diabetes). Acceptance criteria are written as Gherkin scenarios that map 1-to-1 to Pytest or Playwright steps.

---

## Authentication & Onboarding

**US-01-ONB: Sign up with email and password**
Epic: Authentication & Onboarding
Phase: 4, 15

As a Patient,
I want to create an account using my email and a password,
so that my future suggestions and lab history are tied to a personal account I can access from any device.

**Acceptance Criteria**

Scenario: Submitting a valid email and password creates a pending account
  Given the Patient is on the sign-up page
  When  the Patient submits a valid email and a password that meets the policy
  Then  the Patient is redirected to the email-confirmation page

Scenario: Submitting a weak password shows an inline policy error
  Given the Patient is on the sign-up page
  When  the Patient submits a password that does not meet the policy
  Then  an inline error describing the missing requirement appears on the password field
  And   the form does not submit

**Notes**
- Password policy is enforced by AWS Cognito; the UI mirrors its rules.

---

**US-02-ONB: Confirm account via email code**
Epic: Authentication & Onboarding
Phase: 15

As a Patient,
I want to confirm my email address with a verification code,
so that I can recover my account by email if I ever lose access to it.

**Acceptance Criteria**

Scenario: Submitting a valid confirmation code activates the account
  Given the Patient has just signed up and received a verification code by email
  When  the Patient enters the correct code on the confirmation page
  Then  the Patient is redirected to the sign-in page with a success message

Scenario: Submitting an invalid confirmation code shows an inline error
  Given the Patient is on the confirmation page
  When  the Patient enters an incorrect or expired code
  Then  an inline error message is shown on the code field
  And   the account remains unconfirmed

---

**US-03-ONB: Sign in to an existing account**
Epic: Authentication & Onboarding
Phase: 4, 15

As a Patient,
I want to sign in with my confirmed credentials,
so that I can access my personalised suggestions and lab history from any device.

**Acceptance Criteria**

Scenario: Signing in with valid credentials lands on the onboarding or home screen
  Given the Patient has a confirmed account
  When  the Patient submits valid credentials on the sign-in page
  Then  the Patient is redirected to the onboarding flow if the profile is incomplete, or to the home screen otherwise

Scenario: Signing in with wrong credentials is rejected without revealing which field failed
  Given the Patient is on the sign-in page
  When  the Patient submits an incorrect email or password
  Then  a generic "invalid credentials" error is shown
  And   the Patient remains on the sign-in page

---

**US-04-ONB: Complete the nutritional onboarding profile**
Epic: Authentication & Onboarding
Phase: 6, 16

As a Patient,
I want to record my diabetes type, medications, allergies, intolerances, rejected foods, and cultural preferences in a guided form,
so that every future suggestion and recipe respects what I can and want to eat.

**Acceptance Criteria**

Scenario: Submitting a complete profile creates the nutritional profile and unlocks suggestions
  Given the Patient is signed in and the onboarding flow is open at step 1
  When  the Patient fills every step (diagnosis, medications, allergies, intolerances, rejected foods, preferences) and submits
  Then  the Patient is redirected to the suggestions screen
  And   the home screen no longer prompts the Patient to complete onboarding

Scenario: Re-submitting onboarding updates the existing profile instead of creating a duplicate
  Given the Patient already has a saved nutritional profile
  When  the Patient completes the onboarding flow again with changed values
  Then  the profile reflects the new values
  And   no duplicate profile is created for the Patient

---

**US-05-ONB: Resume onboarding after a mid-flow refresh**
Epic: Authentication & Onboarding
Phase: 16

As a Patient,
I want my partially filled onboarding answers to survive an accidental page refresh,
so that I do not have to re-enter sensitive information from scratch.

**Acceptance Criteria**

Scenario: Refreshing mid-flow restores the previously entered values
  Given the Patient has filled the first three onboarding steps without submitting
  When  the Patient refreshes the browser
  Then  the Patient is returned to the same step
  And   the previously entered values are pre-populated

Scenario: Signing out before submitting discards the partial onboarding answers
  Given the Patient has partial onboarding answers stored on the device
  When  the Patient signs out
  Then  the partial answers are cleared from the device
  And   starting onboarding again begins from step 1 with empty fields

---

## Ingredient Suggestions

**US-01-SUG: Request alternatives for an ingredient**
Epic: Ingredient Suggestions
Phase: 9, 17

As a Patient,
I want to ask for nutritionally equivalent alternatives to an ingredient,
so that I can replace foods I cannot or do not want to eat without losing nutritional balance.

**Acceptance Criteria**

Scenario: Requesting alternatives returns three or four options for a valid ingredient
  Given the Patient has completed onboarding and is on the suggestions screen
  When  the Patient requests alternatives for "salmón"
  Then  the suggestions screen shows between three and four alternative ingredients

Scenario: The system fails loudly when fewer than three alternatives can be produced
  Given the Patient has completed onboarding and is on the suggestions screen
  When  the Patient requests alternatives and the engine can only produce two
  Then  the Patient sees an error state asking to try again
  And   no padded or placeholder alternatives are displayed

---

**US-02-SUG: Reject an ingredient from the suggestions**
Epic: Ingredient Suggestions
Phase: 7, 17

As a Patient,
I want to reject an ingredient I do not want to eat,
so that GlucoChef stops offering it to me in future suggestions.

**Acceptance Criteria**

Scenario: Rejecting an ingredient removes it from the current suggestions list
  Given the Patient is viewing a list of alternatives that includes "atún"
  When  the Patient taps Reject on "atún"
  Then  "atún" disappears from the visible suggestions list

Scenario: Rejecting the same ingredient twice in different capitalisations is treated as one rejection
  Given the Patient has already rejected "salmón"
  When  the Patient rejects "Salmón " (different case and trailing whitespace)
  Then  the rejected-ingredients list still contains a single entry for that ingredient

---

**US-03-SUG: Rejected ingredients never reappear in future suggestions**
Epic: Ingredient Suggestions
Phase: 7, 9

As a Patient,
I want previously rejected ingredients to be excluded from every future suggestion,
so that I never have to dismiss the same food twice.

**Acceptance Criteria**

Scenario: A rejected ingredient is absent from the next suggestion response
  Given the Patient has previously rejected "atún"
  When  the Patient requests alternatives for any ingredient
  Then  the returned alternatives do not include "atún"
  But   the rejected ingredient does not reappear in the list

Scenario: Rejected ingredients survive sign-out and sign-in
  Given the Patient rejected "atún" in a previous session
  When  the Patient signs in again and requests alternatives for any ingredient
  Then  the returned alternatives do not include "atún"

---

**US-04-SUG: Alternatives respect declared allergies**
Epic: Ingredient Suggestions
Phase: 9

As a Patient,
I want every suggested alternative to be free of my declared allergens,
so that I can trust the recommendations without rechecking each ingredient.

**Acceptance Criteria**

Scenario: Alternatives exclude all declared allergens
  Given the Patient declared "peanut" and "shellfish" allergies during onboarding
  When  the Patient requests alternatives for "pollo"
  Then  none of the returned alternatives contain peanut or shellfish

Scenario: Adding a new allergy updates the next suggestion response
  Given the Patient has already received suggestions and is editing the profile
  When  the Patient adds "egg" to declared allergies and requests new alternatives
  Then  none of the new alternatives contain egg

---

## Recipe Generation

**US-01-RCP: Generate a recipe from accepted ingredients**
Epic: Recipe Generation
Phase: 10, 18

As a Patient,
I want to generate a recipe from the ingredients I have accepted,
so that I get a concrete meal I can cook tonight using food I already approved.

**Acceptance Criteria**

Scenario: Generating a recipe with accepted ingredients returns a usable recipe
  Given the Patient has accepted at least three ingredients on the suggestions screen
  When  the Patient taps Generate Recipe
  Then  the Patient is taken to a recipe page that shows a title, an ingredient list, step-by-step instructions, and a nutrition summary

Scenario: Generating a recipe with no accepted ingredients is blocked
  Given the Patient has not accepted any ingredient
  When  the Patient taps Generate Recipe
  Then  the Generate Recipe action is disabled
  And   a helper message asks the Patient to accept at least one ingredient first

---

**US-02-RCP: View a complete recipe with nutrition summary**
Epic: Recipe Generation
Phase: 18

As a Patient,
I want every generated recipe to display its ingredients, steps, and nutritional summary,
so that I can decide whether the meal fits my plan before I start cooking.

**Acceptance Criteria**

Scenario: All four recipe blocks are visible on the recipe page
  Given a recipe has been generated for the Patient
  When  the Patient opens the recipe page
  Then  the page shows the title, the ingredient list, the step-by-step instructions, and the nutrition summary

Scenario: Opening a recipe that does not belong to the Patient is rejected
  Given the Patient is signed in
  When  the Patient tries to open a recipe id that belongs to another account
  Then  the page shows a "not found" state
  And   no recipe content is displayed

---

**US-03-RCP: Generate a recipe before any lab entries exist**
Epic: Recipe Generation
Phase: 10

As a Patient,
I want to generate recipes even before I have logged any lab values,
so that I am not blocked from using the product on day one.

**Acceptance Criteria**

Scenario: A recipe is generated without lab data
  Given the Patient has completed onboarding and has not logged any lab entry
  When  the Patient generates a recipe from accepted ingredients
  Then  the recipe page renders successfully with all four blocks

Scenario: A later lab entry does not retroactively alter the existing recipe
  Given the Patient generated a recipe before logging any lab entry
  When  the Patient logs a lab entry afterwards
  Then  the previously generated recipe still shows its original content

---

## Lab Results

**US-01-LAB: Log a lab entry with the four canonical metrics**
Epic: Lab Results
Phase: 11, 19

As a Patient,
I want to manually enter my latest HbA1c, fasting glucose, total cholesterol, and triglycerides,
so that I can track how my numbers evolve over time without needing my doctor to interpret them for me.

**Acceptance Criteria**

Scenario: Submitting all four valid lab values saves the entry and returns to the lab trends page
  Given the Patient is signed in and the lab entry form is open
  When  the Patient enters an HbA1c of 7.2%, a fasting glucose of 110 mg/dL, a total cholesterol of 190 mg/dL, triglycerides of 140 mg/dL, today's date, and submits
  Then  the lab trends page shows the new entry with the four values and the correct date

Scenario: Submitting the form with the HbA1c field empty is blocked
  Given the Patient is signed in and the lab entry form is open
  When  the Patient submits without entering an HbA1c value
  Then  an inline error appears on the HbA1c field
  And   the form does not submit

---

**US-02-LAB: Reject invalid lab values via inline validation**
Epic: Lab Results
Phase: 11, 19

As a Patient,
I want the form to reject impossible lab values inline,
so that I cannot accidentally corrupt my own trend chart with a typo.

**Acceptance Criteria**

Scenario: Entering an out-of-range HbA1c shows an inline validation error
  Given the lab entry form is open
  When  the Patient enters an HbA1c of 25% (above the valid range of 3–20%)
  Then  an inline error message is shown on the HbA1c field
  And   the form does not submit

Scenario: Entering a negative glucose value is rejected before submission
  Given the lab entry form is open
  When  the Patient enters a fasting glucose of -10 mg/dL
  Then  an inline error message is shown on the glucose field
  And   the submit button remains disabled

---

**US-03-LAB: View traffic-light status for each lab metric**
Epic: Lab Results
Phase: 12, 20

As a Patient,
I want each of my lab metrics to be shown with a green, amber, or red status and a plain-language interpretation,
so that I can understand my results at a glance without medical training.

**Acceptance Criteria**

Scenario: A healthy HbA1c is shown with a green status and an encouraging message
  Given the Patient has logged a lab entry with an HbA1c of 6.0%
  When  the Patient opens the lab trends page
  Then  the HbA1c card shows a green status indicator
  And   the card displays a plain-language interpretation describing the value as in range

Scenario: An elevated HbA1c is shown with a red status and a clear warning
  Given the Patient has logged a lab entry with an HbA1c of 9.5%
  When  the Patient opens the lab trends page
  Then  the HbA1c card shows a red status indicator
  And   the card displays a plain-language interpretation describing the value as out of range

---

**US-04-LAB: View the trend across recent lab entries**
Epic: Lab Results
Phase: 12, 20

As a Patient,
I want to see the direction of my latest three lab entries,
so that I know whether my numbers are improving, stable, or worsening over time.

**Acceptance Criteria**

Scenario: Three consecutively worsening HbA1c entries produce a worsening trend
  Given the Patient has logged three HbA1c entries of 6.5%, 7.2%, and 8.1% in order
  When  the Patient opens the lab trends page
  Then  the HbA1c card shows a trend direction of "worsening"

Scenario: Fewer than three lab entries hide the trend indicator
  Given the Patient has logged only two HbA1c entries
  When  the Patient opens the lab trends page
  Then  the HbA1c card does not show a trend direction
  And   a helper message explains that at least three entries are required

---

## Diet–Clinical Correlation

**US-01-COR: Recommendations tighten when labs are red**
Epic: Diet–Clinical Correlation
Phase: 13

As a Patient,
I want my recommendations to adjust automatically when my labs are out of range,
so that the product helps me improve instead of repeating advice that is not working.

**Acceptance Criteria**

Scenario: A red HbA1c tightens the carb guidance in the next recipe
  Given the Patient's latest HbA1c entry shows a red status
  When  the Patient generates a recipe
  Then  the recipe page displays a "carb-restricted" badge in the nutrition summary
  And   the carbohydrate target shown is at most 45 g per serving

Scenario: A red HbA1c also tightens the next ingredient suggestions
  Given the Patient's latest HbA1c entry shows a red status
  When  the Patient requests alternatives for "arroz blanco"
  Then  the returned alternatives do not include white rice, white bread, sugary drinks, or any other ingredient flagged as a refined-carb staple

---

**US-02-COR: Recommendations stay neutral when all labs are green**
Epic: Diet–Clinical Correlation
Phase: 13

As a Patient,
I want recommendations to stop tightening once my labs return to normal,
so that I am not over-restricted when my numbers are already healthy.

**Acceptance Criteria**

Scenario: All-green labs produce baseline recipe guidance
  Given the Patient's latest lab entries are all green
  When  the Patient generates a recipe
  Then  the recipe page does not display a "carb-restricted" badge
  And   the carbohydrate target shown is the baseline value defined for green-state recipes

Scenario: Returning from red to green removes the previous tightening
  Given the Patient had red labs in the previous entry and the new entry is green
  When  the Patient generates a recipe after logging the new entry
  Then  the new recipe page does not display a "carb-restricted" badge
  But   the previously generated recipe is unchanged

---

## PWA & Mobile Experience

**US-01-PWA: Install the app from the browser**
Epic: PWA & Mobile Experience
Phase: 21

As a Patient,
I want to install GlucoChef from my mobile browser,
so that I can open it from my home screen like any other app, without downloading from a store.

**Acceptance Criteria**

Scenario: A supported mobile browser shows an install prompt
  Given the Patient visits the GlucoChef site on a supported mobile browser
  When  the browser evaluates the install criteria
  Then  the Lighthouse PWA audit returns an installability pass

Scenario: After install, the app icon is present on the device home screen
  Given the Patient has accepted the install prompt
  When  the Patient returns to the device home screen
  Then  Manual: locate the GlucoChef icon on the home screen → icon is visible and labelled "GlucoChef"

---

**US-02-PWA: Launch the app full-screen with splash and icon**
Epic: PWA & Mobile Experience
Phase: 21

As a Patient,
I want the installed app to launch full-screen with a splash screen,
so that the experience feels native and the browser chrome does not distract me.

**Acceptance Criteria**

Scenario: Launching the installed app shows the splash screen and no address bar
  Given the Patient has installed GlucoChef on a mobile device
  When  the Patient launches the app from the home-screen icon
  Then  Manual: observe the launch sequence → a splash screen is shown, followed by the app rendered full-screen without an address bar

Scenario: Authenticated routes are not cached by the service worker
  Given the Patient has signed in and used the app while online
  When  the device goes offline and the Patient navigates to a lab or recipe route
  Then  Manual: open the route while offline → no PHI is rendered from the cache

---

## Security & Compliance

**US-01-SEC: PHI is unreadable in the database without the application key**
Epic: Security & Compliance
Phase: 5

As a Patient,
I want my health information stored in a way that cannot be read directly from the database,
so that a leaked database dump does not expose my medical history.

**Acceptance Criteria**

Scenario: Raw database rows for PHI fields are ciphertext
  Given the Patient has logged a lab entry with an HbA1c of 7.2%
  When  the lab row is read directly from the database without the application
  Then  the stored HbA1c value is not equal to "7.2"
  And   the value cannot be reconstructed without the application's encryption key

Scenario: The same value round-trips correctly through the application
  Given the Patient has logged a lab entry with an HbA1c of 7.2%
  When  the Patient reopens the lab trends page
  Then  the HbA1c card shows the original value of 7.2%

---

**US-02-SEC: PHI endpoints reject unauthenticated requests**
Epic: Security & Compliance
Phase: 4, 5

As a Patient,
I want every health-data endpoint to require a valid session,
so that my information cannot be accessed by anyone who guesses a URL.

**Acceptance Criteria**

Scenario: An unauthenticated request to a PHI endpoint is rejected
  Given there is no active session
  When  a request is made to a PHI endpoint such as the lab history
  Then  the response status is 401
  And   no PHI data is returned in the response body

Scenario: A request with an expired session token is rejected
  Given the Patient's session token has expired
  When  a request is made to a PHI endpoint with that token
  Then  the response status is 401
  And   no PHI data is returned in the response body

---

**US-03-SEC: Explicit consent before storing health information**
Epic: Security & Compliance
Phase: 6

As a Patient,
I want to give explicit consent before the app stores any of my health information,
so that I remain in control of what is captured and why.

**Acceptance Criteria**

Scenario: Submitting onboarding without consent is blocked
  Given the Patient is on the final step of onboarding and the consent checkbox is unchecked
  When  the Patient submits the form
  Then  an inline message asks the Patient to acknowledge the consent statement
  And   no nutritional profile is created

Scenario: Submitting onboarding with consent records the consent event
  Given the Patient has filled the onboarding steps and checked the consent statement
  When  the Patient submits the form
  Then  the nutritional profile is created
  And   an audit log entry records the consent action with the Patient's id and a timestamp

---

**US-04-SEC: PHI access is recorded in the audit log**
Epic: Security & Compliance
Phase: 5

As a Patient,
I want every access to my health data to be recorded,
so that any unauthorised look-up could be detected after the fact.

**Acceptance Criteria**

Scenario: Reading the lab trends page creates one audit log entry
  Given the Patient is signed in
  When  the Patient opens the lab trends page
  Then  exactly one audit log entry is created with the Patient's id, the action "read labs", and a timestamp

Scenario: An attempt to read another patient's PHI is recorded as denied
  Given the Patient is signed in
  When  the Patient attempts to read a lab entry that belongs to another account
  Then  the response status is 403
  And   an audit log entry is created with the Patient's id, the action "denied read labs", and a timestamp
