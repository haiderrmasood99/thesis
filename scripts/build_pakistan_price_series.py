#!/usr/bin/env python3
"""
Build yearly Pakistan crop and fertilizer nutrient price series.

Outputs:
    cyclesgym/data/pricing/pakistan_yearly_series.json

Data sources:
1) FAOSTAT Prices (Pakistan producer prices, LCU/tonne)
   https://fenixservices.fao.org/faostat/static/bulkdownloads/Prices_E_All_Data_(Normalized).zip
2) NFDC fertilizer prices table (Rs per 50kg bag)
   https://nfdc.gov.pk/Web-Page%20Updating/prices.htm
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import io
import json
import re
import zipfile

import pandas as pd
import requests
from bs4 import BeautifulSoup


FAOSTAT_PRICES_ZIP_URL = (
    "https://fenixservices.fao.org/faostat/static/bulkdownloads/"
    "Prices_E_All_Data_(Normalized).zip"
)
NFDC_PRICES_URL = "https://nfdc.gov.pk/Web-Page%20Updating/prices.htm"

YEAR_MIN = 1980
YEAR_MAX = 2025

P2O5_TO_P = 0.4364
K2O_TO_K = 0.8301

# Proxy for maize silage fresh-tonne value from grain-tonne producer price.
# This replaces legacy US ratio usage with a Pakistan-series-linked proxy.
SILAGE_TO_GRAIN_PROXY_RATIO = 0.35


@dataclass
class FertilizerBagSeries:
    urea: dict[int, float]
    dap_18_46: dict[int, float]
    sop: dict[int, float]


def _to_float_or_none(value: str | float | int) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        x = float(value)
        return None if x <= 0 else x
    s = str(value).strip().replace(",", "")
    if s in {"", "-", "nan", "NaN", "None"}:
        return None
    try:
        x = float(s)
    except ValueError:
        return None
    return None if x <= 0 else x


def _parse_nfdc_effective_year(token: str) -> int | None:
    s = token.strip()

    m = re.match(r"^(\d{2})-(\d{2})-(\d{2})$", s)
    if m:
        yy = int(m.group(3))
        return 2000 + yy if yy < 50 else 1900 + yy

    m = re.match(r"^(\d{4})-(\d{2})$", s)
    if m:
        start = int(m.group(1))
        yy2 = int(m.group(2))
        century = (start // 100) * 100
        end = century + yy2
        if end < start:
            end += 100
        return end

    return None


def _fetch_nfdc_bag_prices() -> FertilizerBagSeries:
    resp = requests.get(NFDC_PRICES_URL, timeout=90)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    rows = soup.find_all("tr")

    raw: list[tuple[int, float | None, float | None, float | None]] = []
    for row in rows:
        cells = [c.get_text(" ", strip=True) for c in row.find_all(["td", "th"])]
        if len(cells) < 8:
            continue
        year = _parse_nfdc_effective_year(cells[0])
        if year is None:
            continue

        # Relevant columns in NFDC table:
        # 0=effective date, 1=urea, 6=dap, 7=sop
        urea = _to_float_or_none(cells[1])
        dap = _to_float_or_none(cells[6])
        sop = _to_float_or_none(cells[7])
        raw.append((year, urea, dap, sop))

    raw.sort(key=lambda x: x[0])
    by_year: dict[int, tuple[float | None, float | None, float | None]] = {}
    for year, urea, dap, sop in raw:
        prev = by_year.get(year, (None, None, None))
        by_year[year] = (
            urea if urea is not None else prev[0],
            dap if dap is not None else prev[1],
            sop if sop is not None else prev[2],
        )

    urea_s: dict[int, float] = {}
    dap_s: dict[int, float] = {}
    sop_s: dict[int, float] = {}
    last_urea = last_dap = last_sop = None

    for year in range(YEAR_MIN, YEAR_MAX + 1):
        if year in by_year:
            y_urea, y_dap, y_sop = by_year[year]
            if y_urea is not None:
                last_urea = y_urea
            if y_dap is not None:
                last_dap = y_dap
            if y_sop is not None:
                last_sop = y_sop

        if last_urea is not None:
            urea_s[year] = float(last_urea)
        if last_dap is not None:
            dap_s[year] = float(last_dap)
        if last_sop is not None:
            sop_s[year] = float(last_sop)

    return FertilizerBagSeries(urea=urea_s, dap_18_46=dap_s, sop=sop_s)


def _extract_faostat_item_series(
    df: pd.DataFrame,
    item_name: str,
) -> tuple[dict[int, float], dict[int, float]]:
    item_df = df[df["Item"] == item_name]
    price_df = item_df[item_df["Element Code"] == 5530][["Year", "Value"]]
    idx_df = item_df[item_df["Element Code"] == 5539][["Year", "Value"]]
    price_series = {int(r["Year"]): float(r["Value"]) for _, r in price_df.iterrows()}
    idx_series = {int(r["Year"]): float(r["Value"]) for _, r in idx_df.iterrows()}
    return price_series, idx_series


def _fill_with_price_index(
    annual_price: dict[int, float],
    price_index: dict[int, float],
    year_min: int,
    year_max: int,
) -> dict[int, float]:
    years = list(range(year_min, year_max + 1))
    known = {y: annual_price[y] for y in sorted(annual_price.keys()) if y in price_index}
    out: dict[int, float | None] = {y: annual_price.get(y) for y in years}

    for y in years:
        if out[y] is not None:
            continue
        idx_y = price_index.get(y)
        if idx_y is None or not known:
            continue

        # Use closest anchor year where both annual price and index exist.
        anchor = min(known.keys(), key=lambda k: abs(k - y))
        anchor_idx = price_index.get(anchor)
        if anchor_idx is None or anchor_idx <= 0:
            continue
        out[y] = known[anchor] * (idx_y / anchor_idx)

    # Nearest-neighbor fill if a year still has no data.
    final: dict[int, float] = {}
    valid_years = [y for y in years if out[y] is not None]
    if not valid_years:
        return final
    for y in years:
        if out[y] is not None:
            final[y] = float(out[y])
            continue
        nearest = min(valid_years, key=lambda k: abs(k - y))
        final[y] = float(out[nearest])
    return final


def _fetch_faostat_crop_prices() -> tuple[dict[int, float], dict[int, float]]:
    resp = requests.get(FAOSTAT_PRICES_ZIP_URL, timeout=180)
    resp.raise_for_status()
    zf = zipfile.ZipFile(io.BytesIO(resp.content))
    csv_name = next(name for name in zf.namelist() if name.endswith(".csv"))

    frames: list[pd.DataFrame] = []
    usecols = ["Area", "Item", "Element Code", "Year", "Months", "Value"]
    for chunk in pd.read_csv(zf.open(csv_name), encoding="latin1", usecols=usecols, chunksize=250_000):
        filtered = chunk[
            (chunk["Area"] == "Pakistan")
            & (chunk["Item"].isin(["Maize (corn)", "Soya beans"]))
            & (chunk["Months"] == "Annual value")
            & (chunk["Element Code"].isin([5530, 5539]))
        ]
        if not filtered.empty:
            frames.append(filtered)

    if not frames:
        raise RuntimeError("No Pakistan crop rows found in FAOSTAT price data.")

    df = pd.concat(frames, ignore_index=True)
    maize_price, maize_idx = _extract_faostat_item_series(df, "Maize (corn)")
    soy_price, soy_idx = _extract_faostat_item_series(df, "Soya beans")

    maize = _fill_with_price_index(maize_price, maize_idx, YEAR_MIN, YEAR_MAX)
    soy = _fill_with_price_index(soy_price, soy_idx, YEAR_MIN, YEAR_MAX)
    return maize, soy


def _bag_price_to_rs_per_kg_nutrient(price_rs_per_50kg_bag: float, nutrient_fraction: float) -> float:
    if nutrient_fraction <= 0:
        raise ValueError("nutrient_fraction must be > 0")
    return float(price_rs_per_50kg_bag) / (50.0 * float(nutrient_fraction))


def _build_payload() -> dict:
    maize, soy = _fetch_faostat_crop_prices()
    fert = _fetch_nfdc_bag_prices()

    n_price = {
        y: _bag_price_to_rs_per_kg_nutrient(v, nutrient_fraction=0.46)
        for y, v in fert.urea.items()
    }
    p_price = {
        y: _bag_price_to_rs_per_kg_nutrient(v, nutrient_fraction=0.46 * P2O5_TO_P)
        for y, v in fert.dap_18_46.items()
    }
    k_price = {
        y: _bag_price_to_rs_per_kg_nutrient(v, nutrient_fraction=0.50 * K2O_TO_K)
        for y, v in fert.sop.items()
    }

    silage = {y: maize[y] * SILAGE_TO_GRAIN_PROXY_RATIO for y in maize.keys()}

    payload = {
        "metadata": {
            "generated_utc": datetime.now(timezone.utc).isoformat(),
            "sources": {
                "faostat_prices_zip": FAOSTAT_PRICES_ZIP_URL,
                "nfdc_prices_table": NFDC_PRICES_URL,
            },
            "notes": [
                "Maize/Soya producer prices are Pakistan annual LCU/tonne series from FAOSTAT.",
                "Missing annual price years are reconstructed using FAOSTAT producer price index (2014-2016=100).",
                "NFDC fertilizer product prices are converted to nutrient-basis Rs/kg for N, P, K.",
                "Corn silage uses a Pakistan-linked maize proxy with fixed fresh-tonne conversion ratio.",
            ],
            "silage_proxy_ratio": SILAGE_TO_GRAIN_PROXY_RATIO,
            "conversion_factors": {
                "P2O5_to_P": P2O5_TO_P,
                "K2O_to_K": K2O_TO_K,
            },
        },
        "crop_prices_lcu_per_tonne": {
            "maize": {str(y): round(v, 6) for y, v in sorted(maize.items())},
            "soybeans": {str(y): round(v, 6) for y, v in sorted(soy.items())},
            "maize_silage_proxy": {str(y): round(v, 6) for y, v in sorted(silage.items())},
        },
        "fertilizer_product_prices_rs_per_50kg_bag": {
            "urea": {str(y): round(v, 6) for y, v in sorted(fert.urea.items())},
            "dap_18_46": {str(y): round(v, 6) for y, v in sorted(fert.dap_18_46.items())},
            "sop": {str(y): round(v, 6) for y, v in sorted(fert.sop.items())},
        },
        "nutrient_prices_rs_per_kg": {
            "N": {str(y): round(v, 6) for y, v in sorted(n_price.items())},
            "P": {str(y): round(v, 6) for y, v in sorted(p_price.items())},
            "K": {str(y): round(v, 6) for y, v in sorted(k_price.items())},
        },
    }
    return payload


def main():
    repo_root = Path(__file__).resolve().parents[1]
    out_path = repo_root / "cyclesgym" / "resources" / "pricing" / "pakistan_yearly_series.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    payload = _build_payload()
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote: {out_path}")


if __name__ == "__main__":
    main()
