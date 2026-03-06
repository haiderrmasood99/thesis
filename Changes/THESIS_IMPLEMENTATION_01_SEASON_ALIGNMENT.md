# Thesis Implementation Update 01: Pakistan Crop-Season Alignment

- Date: 2026-03-06
- Goal started from roadmap: make crop-planning actions more Pakistan-season aware without breaking existing experiments.

## What I Implemented

1. Added a new Pakistan crop-calendar utility:
   - `cyclesgym/utils/pakistan_crop_calendar.py`
   - Contains:
     - model-crop to sowing-window mapping (DOY ranges),
     - source metadata links used for those windows,
     - helper function to pull windows only for crops in the active rotation.

2. Added optional season-aware behavior to crop planning env:
   - `cyclesgym/envs/crop_planning.py`
   - New optional args:
     - `use_pakistan_crop_calendar=False` (default off),
     - `crop_calendar_windows=None`.
   - If enabled, crop windows are injected into the planter implementer.

3. Extended `RotationPlanter` to support calendar windows:
   - `cyclesgym/envs/implementers.py`
   - New features:
     - validates window ranges,
     - maps action week index to crop-specific DOY window when configured,
     - keeps old legacy mapping if crop has no configured window.

4. Added/updated tests:
   - `cyclesgym/tests/test_implementers.py`
   - New tests verify:
     - default mapping remains unchanged,
     - configured crop uses Pakistan window mapping,
     - non-configured crop safely falls back to old behavior,
     - invalid windows raise assertion.

## Why This Matters (Layman Terms)

In simple terms: the model should not suggest planting a crop in a season when farmers in Pakistan do not plant it.  
This update makes it possible to guide the RL model toward realistic planting windows (for example, maize/wheat seasonality), so recommendations are more practical for real farming decisions.

## Thesis Relevance

This directly supports:

1. **Agronomic realism**: decisions align better with Pakistan crop seasons.
2. **Defensibility**: recommendations are easier to justify in a thesis defense because they are tied to documented calendars.
3. **Integrity**: old behavior is preserved unless you explicitly enable season mode.

## Integrity & Safety Controls Used

1. Backward compatibility:
   - Default behavior stays exactly as before (`use_pakistan_crop_calendar=False`).
2. Controlled rollout:
   - Only configured crops are constrained.
   - Unknown crops automatically use legacy behavior.
3. Input validation:
   - Window must be `(start_doy, end_doy)`,
   - values must be between `1` and `366`,
   - `start_doy <= end_doy`.
4. Test coverage:
   - Added focused unit tests around new mapping behavior.

## Source Links Used

Season references used in implementation metadata:

1. KP Agriculture (Maize production technology):
   - https://zarat.kp.gov.pk/assets/uploads/publications/Maize%20Production%20Technology.pdf
2. PBS crop calendar (Kharif):
   - https://www.pbs.gov.pk/sites/default/files//tables/table_13_approved_crop_calendar_kharif.pdf
3. PBS crop calendar (Rabi):
   - https://www.pbs.gov.pk/sites/default/files/tables/table_14_approved_crop_calendar_rabi.pdf

## APIs / URLs Mentioned for Upcoming Thesis Steps

These were identified for next implementations (weather/soil/data expansion):

1. NASA POWER API:
   - https://power.larc.nasa.gov/docs/services/api/temporal/daily/
2. ISRIC SoilGrids:
   - https://docs.isric.org/globaldata/soilgrids/index.html
3. NFDC fertilizer review publication hub:
   - https://www.mnfsr.gov.pk/publications

## Validation Performed

1. Compile check:
   - `python -m compileall cyclesgym/utils/pakistan_crop_calendar.py cyclesgym/envs/implementers.py cyclesgym/envs/crop_planning.py cyclesgym/tests/test_implementers.py`
   - Result: PASS
2. Unit tests:
   - `pytest cyclesgym/tests/test_implementers.py -q` -> PASS (`8 passed`)
   - `pytest cyclesgym/tests/test_rewarders.py -q` -> PASS (`1 passed`)

## How To Use The New Feature

Example:

```python
from cyclesgym.envs.crop_planning import CropPlanningFixedPlanting

env = CropPlanningFixedPlanting(
    start_year=2005,
    end_year=2018,
    rotation_crops=["CornRM.100", "SoybeanMG.3"],
    use_pakistan_crop_calendar=True,
)
```

If you want full manual control:

```python
custom_windows = {"CornRM.100": (166, 196), "SoybeanMG.3": (166, 196)}
env = CropPlanningFixedPlanting(..., crop_calendar_windows=custom_windows)
```

## Notes

1. This update does not overwrite any existing weather/soil input data files.
2. This is step 1 from the thesis enhancement roadmap; next logical step is NPK/cost localization with Pakistan fertilizer and crop price series.

