# API

Base URL during local run:

```text
http://127.0.0.1:8000
```

## `GET /api/v1/health`

Returns a simple health payload.

Example response:

```json
{
  "status": "ok",
  "curated_bundles": 3
}
```

## `GET /api/v1/options`

Returns UI options, labels, and Urdu hints.

## `POST /api/v1/advice/daily`

Primary guided-assistant endpoint. Soybean requests are automatically downgraded to light-support output.

Example request:

```json
{
  "crop": "maize",
  "crop_stage": "vegetative",
  "land_area_acres": 5,
  "budget_pkr": 120000,
  "prior_fertilizer": {
    "n_kg_per_acre": 0,
    "p_kg_per_acre": 0,
    "k_kg_per_acre": 0
  },
  "soil_condition": "balanced",
  "recent_rain": "moderate",
  "expected_weather": "uncertain",
  "language": "en_pk"
}
```

Key response fields:

- `summary`
- `today_action`
- `next_steps`
- `season_estimate`
- `baseline_comparison`
- `warnings`
- `confidence`
- `explanation`
- `support_level`

## `POST /api/v1/advice/seasonal`

Dedicated soybean/reference endpoint.

Example request:

```json
{
  "crop": "soybean",
  "land_area_acres": 5,
  "budget_pkr": 120000,
  "language": "en_pk"
}
```
