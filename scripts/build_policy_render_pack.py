#!/usr/bin/env python3
"""Rebuild only per-run renders and representative render sets."""

from __future__ import annotations

import argparse
from pathlib import Path

from thesis_reporting_pack_lib import DEFAULT_OUTPUT_ROOT, rebuild_renders_only


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--datasets",
        default="final_113,final_42_ablation",
        help="Comma-separated datasets to rebuild renders for. Default: final_113,final_42_ablation",
    )
    parser.add_argument(
        "--output-root",
        default=str(DEFAULT_OUTPUT_ROOT),
        help=f"Existing thesis reporting pack root. Default: {DEFAULT_OUTPUT_ROOT}",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    datasets = [part.strip() for part in args.datasets.split(",") if part.strip()]
    rebuild_renders_only(datasets=datasets, output_root=Path(args.output_root))


if __name__ == "__main__":
    main()
