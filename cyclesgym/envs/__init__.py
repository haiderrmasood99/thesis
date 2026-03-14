from __future__ import annotations

__all__ = [
    "Corn",
    "CropPlanningFixedPlanting",
    "HierarchicalCropPlanningFertilization",
]


def __getattr__(name: str):
    if name == "Corn":
        from cyclesgym.envs.corn import Corn

        return Corn
    if name == "CropPlanningFixedPlanting":
        from cyclesgym.envs.crop_planning import CropPlanningFixedPlanting

        return CropPlanningFixedPlanting
    if name == "HierarchicalCropPlanningFertilization":
        from cyclesgym.envs.hierarchical import HierarchicalCropPlanningFertilization

        return HierarchicalCropPlanningFertilization
    raise AttributeError(f"module 'cyclesgym.envs' has no attribute {name!r}")
