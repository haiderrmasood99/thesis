#!/usr/bin/env python3
"""Build the immutable thesis reporting pack."""

from __future__ import annotations

import argparse
from pathlib import Path

from thesis_reporting_pack_lib import DEFAULT_OUTPUT_ROOT, build_reporting_pack


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--datasets",
        default="final_113,final_42_ablation",
        help="Comma-separated datasets to build. Default: final_113,final_42_ablation",
    )
    parser.add_argument(
        "--output-root",
        default=str(DEFAULT_OUTPUT_ROOT),
        help=f"Output root for the thesis reporting pack. Default: {DEFAULT_OUTPUT_ROOT}",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Delete and rebuild the output root before generating artifacts.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    datasets = [part.strip() for part in args.datasets.split(",") if part.strip()]
    build_reporting_pack(datasets=datasets, output_root=Path(args.output_root), overwrite=args.overwrite)


if __name__ == "__main__":
    main()
