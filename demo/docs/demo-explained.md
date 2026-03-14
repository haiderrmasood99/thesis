# Farmer-First Pakistan Demo Explained

## Purpose

This document explains the demo app end to end:

- what the demo is trying to show
- all frontend input choices and effective combination paths
- what "guardrails" mean in this project
- how the backend turns form inputs into recommendations
- what users should and should not claim from the output

This app is a local thesis MVP. It is a decision-support demo, not an autonomous agronomy system and not a province-wide production deployment.

## What the Demo Is

The demo is a farmer-facing interface over audited reinforcement learning artifacts stored in `artifacts/final_successful_runs`.

The app has two main product paths:

- `Maize`: full daily-support mode
- `Soybean`: light-support seasonal reference mode

The demo is designed to answer a practical question:

`Given the current crop situation, budget, and recent moisture conditions, what should I do now or this week?`

## What the Demo Is Not

The demo is not:

- a live sensor platform
- a free-text agronomy chatbot
- a fully validated real-world fertilizer prescription engine
- a Pakistan-wide calibrated advisory platform

The output is simulator-backed, then post-processed by safety and practicality rules before it is shown to the farmer.

## High-Level User Flow

1. Open the frontend.
2. Press `Start assistant`.
3. Select crop and crop stage.
4. Enter land size and budget.
5. Enter any prior fertilizer already applied.
6. Select soil condition, recent rain, expected weather, and language.
7. Press `Get advice` for maize-like daily guidance, or `Soybean seasonal reference` for soybean reference mode.
8. Read:
   - the main recommendation
   - warnings
   - next-step cards
   - season estimate
   - comparison against baseline
   - explanation and evidence drawer

## Full Frontend Input Space

### Categorical Inputs

#### Crop

- `maize`
- `soybean`

#### Maize Stages

- `pre_sowing`
- `emergence`
- `vegetative`
- `flowering`
- `grain_fill`
- `maturity`

#### Soybean Stages

- `pre_sowing`
- `vegetative`
- `flowering`
- `pod_fill`
- `maturity`

#### Soil Condition

- `dry`
- `balanced`
- `wet`

#### Recent Rain

- `none`
- `light`
- `moderate`
- `heavy`

#### Expected Weather

- `stable`
- `uncertain`

#### Language

- `en_pk`
- `en`

### Numeric Inputs

#### Land Area

- required
- greater than `0`
- maximum `200` acres

#### Budget

- required
- greater than `0`
- maximum `5,000,000` PKR

#### Prior Fertilizer

Each nutrient is entered in `kg per acre`.

- `n_kg_per_acre`: `0` to `250`
- `p_kg_per_acre`: `0` to `250`
- `k_kg_per_acre`: `0` to `250`

## "All Possible Combos" Explained Properly

There are two different ways to think about combinations:

1. `Visible frontend combinations`
2. `Effective backend combinations`

These are not the same, because some frontend fields are only meaningful for maize and some are ignored in soybean reference mode.

### Visible Categorical Combinations

Ignoring numeric inputs:

- Maize visible categorical combinations:
  - `6 stages x 3 soil states x 4 rain states x 2 weather modes x 2 language modes`
  - total = `288`
- Soybean visible categorical combinations in the daily form:
  - `5 stages x 3 soil states x 4 rain states x 2 weather modes x 2 language modes`
  - total = `240`

Once land area, budget, and prior fertilizer amounts are included, the total combination count is effectively unbounded for practical purposes.

### Effective Backend Combination Families

#### Family 1: Maize Daily Advice

This is the main inference path.

Inputs that matter:

- crop
- crop stage
- land area
- budget
- prior fertilizer
- soil condition
- recent rain
- expected weather
- language

Output:

- full advice response
- `support_level = full`
- daily/weekly action card
- next-step cards
- season estimate
- baseline comparison

#### Family 2: Soybean Through the Daily Form

If the frontend sends `crop = soybean` to the daily endpoint, the backend immediately reroutes it to the soybean light-support path.

Important detail:

- soybean stage is validated, but not used for the recommendation logic
- soil condition is ignored
- recent rain is ignored
- expected weather is ignored
- prior fertilizer is ignored

Effective soybean inputs are only:

- land area
- budget
- language

Output:

- `support_level = light`
- no true daily fertilizer dose
- reference cards only

#### Family 3: Dedicated Soybean Seasonal Reference Button

This calls the seasonal endpoint directly.

Effective inputs:

- land area
- budget
- language

Output:

- same light-support soybean reference behavior

## Exact Decision Logic by Input Family

### Crop Switch

#### If Crop Is `maize`

The backend performs actual local model inference and then applies guardrails.

#### If Crop Is `soybean`

The backend uses audited hierarchical report data and returns a reference-style response only.

## Maize Combination Logic

### Stage Logic

The backend maps stage to a position in the maize episode timeline:

- `pre_sowing` -> start of season
- `emergence` -> early season
- `vegetative` -> early-mid season
- `flowering` -> mid season
- `grain_fill` -> late season
- `maturity` -> very late season

Internally, the current stage is converted into a week index in the simulated episode.

### Weather Logic

#### `stable`

Uses the curated fixed-weather maize bundle:

- `Fertilization | PPO | adaptive | fixed_weather | years=1000 | seed=0`

#### `uncertain`

Uses the curated random-weather maize bundle:

- `Fertilization | PPO | adaptive | random_weather | years=1000 | seed=0`

This path also adds a warning that the result should be treated as guarded guidance under uncertainty.

### Soil and Rain Logic

These fields do not change which bundle is loaded. They change the post-processing guardrails.

#### Dry Soil + No Rain or Light Rain

Rule:

- if `soil_condition = dry`
- and `recent_rain` is `none` or `light`

Effect:

- current recommendation becomes `wait`
- today's nutrient dose is set to zero
- the original dose is shifted into the next-step card

Reason:

- the app is intentionally trying to avoid telling a farmer to fertilize into dry conditions with poor moisture support

#### Wet Soil + Heavy Rain

Rule:

- if `soil_condition = wet`
- and `recent_rain = heavy`

Effect:

- status becomes `watch`
- today's nutrient amount is reduced:
  - N multiplied by `0.60`
  - P multiplied by `0.85`
  - K multiplied by `0.90`

Reason:

- heavy moisture increases nutrient loss risk, especially for nitrogen

#### All Other Soil/Rain Combinations

The app keeps the stage-mapped policy action, then still applies weekly cap, season cap, and budget rules.

## Budget Combination Logic

Budget logic is one of the main guardrails.

### Step 1: Remaining Budget

The backend first estimates the cost of prior fertilizer already entered by the user.

Then it computes:

`remaining budget = entered budget - estimated prior fertilizer cost`

### Step 2: Budget Guardrail

If remaining budget is `<= 0`:

- status becomes `wait`
- today becomes zero
- next steps become zero
- season estimate becomes zero

If season estimate cost is greater than remaining budget:

- the entire recommendation is scaled down by a ratio
- status becomes at least `watch`

This means the policy does not get to spend the user's budget freely. The demo forces the output to respect the financial constraint.

## What Guardrails Mean

### Simple Definition

Guardrails are hard safety and practicality rules applied after the model generates a recommendation.

The model says:

- "in this simulator state, this action is good"

The guardrails say:

- "fine, but do not show anything that is too aggressive, too expensive, too wet-soil risky, or too dry-soil risky"

### Why Guardrails Exist

The underlying RL policy was trained in simulation. Simulator-optimized actions can be:

- too aggressive for a farmer-facing interface
- too expensive for the entered budget
- too risky under certain moisture situations

So the demo deliberately clamps the output before showing it.

### Guardrails Used in This Demo

#### Weekly Cap

Maize weekly doses are clipped to:

- `N = 55 kg/ha`
- `P = 28 kg/ha`
- `K = 24 kg/ha`

#### Season Cap

Remaining maize season estimate is clipped to:

- `N = 180 kg/ha`
- `P = 78 kg/ha`
- `K = 65 kg/ha`

Soybean seasonal reference is clipped to:

- `N = 60 kg/ha`
- `P = 38 kg/ha`
- `K = 32 kg/ha`

#### Moisture Guardrail

- dry + low rain -> `wait`
- wet + heavy rain -> reduce and `watch`

#### Budget Guardrail

- no budget left -> zero recommendation and `wait`
- recommendation too expensive -> scale down and `watch`

#### Uncertain Weather Guardrail

- uncertain season adds a warning
- this does not zero the recommendation, but it reduces confidence

## Status Values and What They Mean

### `do_now`

Use the current week action now.

This is the cleanest output state.

### `watch`

The app still sees a possible action, but wants caution.

Typical causes:

- heavy rain on wet soil
- budget scaling

### `wait`

The app is intentionally telling the user not to apply now.

Typical causes:

- dry soil with poor recent rain
- exhausted budget

### `reference`

This is not a daily prescription. It is a planning/reference card.

This is used for soybean light-support mode.

## Confidence Levels

### `high`

Returned when the maize path remains clean after post-processing.

### `medium`

Returned when weather is uncertain but no stronger warning path was triggered.

### `guarded`

Returned when warnings or status changes such as `wait` or `watch` were triggered.

### `low`

Used for soybean light-support reference mode.

## Baseline Comparison

Every main result includes a comparison against a fixed demo baseline.

### Maize Baseline

- `N = 135 kg/ha`
- `P = 58 kg/ha`
- `K = 42 kg/ha`

### Soybean Baseline

- `N = 24 kg/ha`
- `P = 30 kg/ha`
- `K = 18 kg/ha`

The comparison is there to improve trust:

- recommended cost
- baseline cost
- cost delta
- summary text

This is not another learned model. It is a fixed comparison template.

## Technical Architecture

### Frontend

The frontend is a React + Vite single-page app.

Main UI sections:

- hero panel
- guided form assistant
- summary rail
- result panel
- comparison card
- evidence drawer

### Backend

The backend is a FastAPI service.

Public endpoints:

- `GET /api/v1/health`
- `GET /api/v1/options`
- `POST /api/v1/advice/daily`
- `POST /api/v1/advice/seasonal`

### Artifact Discovery

The backend reads:

- `artifacts/final_successful_runs/manifest.csv`

It resolves curated bundles:

- `maize_uncertain`
- `maize_stable`
- `soybean_reference`

### Runtime Adapter

For maize, the runtime adapter:

1. reads bundle metadata from the manifest
2. parses `wandb/config.yaml`
3. loads `model.zip`
4. tries to load normalization stats if compatible
5. builds a fertilization environment matching the bundle config
6. decodes scalar or `MultiDiscrete` actions into NPK masses

### Python 3.8 Compatibility Fallback

The repo's shared `cyclesgym` environment uses Python 3.8.

Some saved SB3 metadata and normalization pickles are not fully portable to that older environment, so the runtime includes a fallback path that:

- loads the model with safe `custom_objects`
- skips incompatible training-state metadata
- runs plain local rollout when `VecNormalize` cannot be restored

This is a runtime compatibility fix, not a change to the thesis logic.

### Reinitialization Disabled for Demo Inference

The original corn environment supports a reinitialization flow across year boundaries.

For this demo, that reinit path is disabled during inference because:

- the demo is a short local recommendation workflow
- the legacy reinit path expected files like `reinit.dat`
- that path caused avoidable failures for frontend requests

This means the demo focuses on stable local inference rather than full training-style simulator lifecycle behavior.

## How Maize Advice Is Produced

1. User submits a maize daily request.
2. Backend selects the stable or uncertain maize bundle.
3. Backend runs local episode inference.
4. Backend maps crop stage to a point in the episode.
5. Backend slices the current step and next steps.
6. Backend builds a remaining-season estimate.
7. Backend applies guardrails.
8. Backend adds a baseline comparison.
9. Backend sends result cards back to the frontend.

## How Soybean Advice Is Produced

1. User selects soybean or presses soybean seasonal reference.
2. Backend reads hierarchical report CSVs from the curated soybean reference bundle.
3. Backend averages historical weekly NPK traces for soybean years.
4. Backend builds reference checkpoints and a seasonal estimate.
5. Backend marks the response as `support_level = light`.

No soybean daily model inference is performed in this MVP.

## Frontend Result Cards Explained

### Main Summary

One-sentence answer shown at the top.

Examples:

- apply a measured top-up
- wait for better moisture
- use a reduced dose

### Warning Pills

These explain why the result was softened or constrained.

Examples:

- dry soil and low rain
- budget scaling
- uncertain weather

### Today's Move

This is the main card for maize.

It shows:

- status
- nutrient dose per hectare
- nutrient dose per acre
- total field amount
- estimated field cost

### Next Steps

These are follow-up scenario cards, not promises.

They help the user understand what the next one or two weeks might look like under the same scenario assumptions.

### Season Estimate

This summarizes the remaining-season nutrient and cost envelope after the current point in the season.

### Compare Plan

This compares the recommendation with a fixed demo baseline.

### Why This Answer

This is a plain-language explanation list.

### Model Evidence

The evidence drawer exposes selected backend metadata such as:

- bundle label
- bundle index
- algorithm method
- whether normalization stats were loaded
- summary metric like Pakistan holdout return

## Recommended Frontend Demo Scenarios

### Best Main Thesis Demo

- crop: `maize`
- stage: `vegetative`
- land area: `5`
- budget: `120000`
- prior fertilizer: `0 / 0 / 0`
- soil: `balanced`
- rain: `moderate`
- weather: `uncertain`

Expected behavior:

- full maize path
- usually a real action card
- clear warning that weather is uncertain

### Guardrail Demo

- crop: `maize`
- stage: `pre_sowing` or `vegetative`
- soil: `dry`
- rain: `none`

Expected behavior:

- `wait`
- today's action moved to follow-up logic

This is good for showing that the app does not always push fertilizer.

### Heavy-Rain Caution Demo

- crop: `maize`
- soil: `wet`
- rain: `heavy`

Expected behavior:

- `watch`
- reduced current dose

### Soybean Demo

- crop: `soybean`
- press `Soybean seasonal reference`

Expected behavior:

- `support_level = light`
- reference cards only

## Known Simplifications and Quirks

### Soybean Form Inputs Are More Detailed Than Soybean Logic

The frontend still shows stage, soil, rain, and weather fields for soybean, but the backend currently does not use them for soybean advice. Soybean is intentionally reference-only in this MVP.

### Language Does Not Change Agronomy

Language only changes presentation and hinting. It does not change the underlying recommendation logic.

### Terminal Warnings May Still Appear

Examples:

- `Gym has been unmaintained...`
- `There is already an operation FIXED_FERTILIZATION...`

These are usually runtime noise rather than user-facing failures.

## What the Demo Can Validly Claim

This demo can claim:

- audited RL artifacts can be translated into a farmer-facing workflow
- recommendations can be constrained by cost and moisture guardrails
- a non-technical user can compare recommendations against a baseline
- the app runs locally without cloud dependency

This demo should not claim:

- province-wide agronomic validation
- direct replacement of agronomists
- guaranteed real-world optimal fertilizer decisions
- raw sensor-grounded, field-proven prescriptions

## Short Thesis Positioning Line

`This demo shows how audited reinforcement learning outputs can be converted into a farmer-facing decision-support experience with guardrails, baseline comparison, local inference, and explicit limitation notes.`
