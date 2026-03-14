from __future__ import annotations

import csv
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from demo.backend.config import (
    MANIFEST_PATH,
    PRIMARY_MAIZE_LABEL,
    SOYBEAN_REFERENCE_LABEL,
    STABLE_MAIZE_LABEL,
)


@dataclass(frozen=True)
class BundleRecord:
    index: int
    label: str
    domain: str
    method: str
    run_id: str
    bundle_dir: Path
    metadata_path: Path
    config_path: Path
    model_path: Path
    stats_path: Path | None
    summary_path: Path | None
    report_dir: Path | None


def _pick_optional_path(bundle_dir: Path, pattern: str) -> Path | None:
    matches = sorted(bundle_dir.glob(pattern))
    return matches[0] if matches else None


def _build_bundle_record(row: dict[str, str]) -> BundleRecord:
    bundle_dir = Path(row["bundle_dir"])
    if not bundle_dir.is_absolute():
        bundle_dir = (MANIFEST_PATH.parents[1] / bundle_dir).resolve()
    return BundleRecord(
        index=int(row["index"]),
        label=row["label"],
        domain=row["domain"],
        method=row["method"],
        run_id=row["run_id"],
        bundle_dir=bundle_dir,
        metadata_path=bundle_dir / "bundle_metadata.json",
        config_path=bundle_dir / "wandb" / "config.yaml",
        model_path=bundle_dir / "models" / "model.zip",
        stats_path=_pick_optional_path(bundle_dir, "runtime/*.pkl"),
        summary_path=_pick_optional_path(bundle_dir, "summary/*.json"),
        report_dir=_pick_optional_path(bundle_dir, "reports/*"),
    )


@lru_cache(maxsize=1)
def load_manifest() -> list[BundleRecord]:
    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(f"Missing bundle manifest: {MANIFEST_PATH}")
    with MANIFEST_PATH.open("r", encoding="utf-8", newline="") as handle:
        return [_build_bundle_record(row) for row in csv.DictReader(handle)]


def get_bundle_by_label(label: str) -> BundleRecord:
    for bundle in load_manifest():
        if bundle.label == label:
            return bundle
    raise KeyError(f"Bundle not found for label: {label}")


@lru_cache(maxsize=1)
def get_curated_bundles() -> dict[str, BundleRecord]:
    return {
        "maize_uncertain": get_bundle_by_label(PRIMARY_MAIZE_LABEL),
        "maize_stable": get_bundle_by_label(STABLE_MAIZE_LABEL),
        "soybean_reference": get_bundle_by_label(SOYBEAN_REFERENCE_LABEL),
    }
