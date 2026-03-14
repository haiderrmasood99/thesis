# User Guide

## Intended User

This MVP is designed for a Pakistani farmer-facing demo. It is easiest to use on a phone-sized screen, but it also works on desktop.

## Main Flow

1. Open the app home screen.
2. Press `Start assistant`.
3. Choose the crop.
4. Choose the crop stage.
5. Enter land area in acres and available budget in PKR.
6. Enter any fertilizer already applied.
7. Select soil condition, recent rain, and expected weather.
8. Press `Get advice`.

## What the App Returns

- a primary recommendation for `This week`
- two follow-up cards for the next checks
- a remaining-season estimate
- a comparison against a fixed baseline plan
- warnings and confidence level

## Maize vs Soybean

- `Maize`: full daily-support mode
- `Soybean`: seasonal reference mode only

## Suggested Demo Scenarios

### Maize Daily Demo

- crop: maize
- crop stage: vegetative
- land area: 5 acres
- budget: 120000 PKR
- soil: balanced
- recent rain: moderate
- weather: uncertain

### Soybean Reference Demo

- crop: soybean
- land area: 5 acres
- budget: 120000 PKR
- use `Soybean seasonal reference`

## Reading the Output

- `do now`: use the recommendation this week
- `watch`: use a reduced dose or monitor moisture before acting
- `wait`: do not apply now; moisture or budget is too tight
- `reference`: a planning card, not a daily instruction
