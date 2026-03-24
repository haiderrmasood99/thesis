import os
import shutil
import json
import pandas as pd
from pathlib import Path

BASE_DIR = Path(r"D:\THESIS FINAL EXPERIMENTS\thesis_backup\thesis")
REPORTING_ROOT = BASE_DIR / "artifacts" / "final_successful_runs" / "thesis_reporting_pack"
PUBLIC_DATA_DIR = BASE_DIR / "thesis_dashboard" / "public" / "data"

DATASETS = ["final_113", "final_42_ablation"]

def main():
    os.makedirs(PUBLIC_DATA_DIR, exist_ok=True)
    
    runs_index = []

    for dataset in DATASETS:
        print(f"Processing {dataset}...")
        ds_root = REPORTING_ROOT / dataset
        ds_public = PUBLIC_DATA_DIR / dataset
        os.makedirs(ds_public, exist_ok=True)
        
        # Load Catalog
        catalog_path = ds_root / "tables" / "grouped" / f"{dataset}__run_catalog.csv"
        if not catalog_path.exists():
            print(f"Missing catalog at {catalog_path}")
            continue
        
        catalog = pd.read_csv(catalog_path)
        
        # Collect per-run metadata
        for _, row in catalog.iterrows():
            run_slug = str(row["run_slug"])
            
            # Map required files
            required_files = [
                f"{run_slug}__history_selected.csv",
                f"{run_slug}__weekly_npk_log.csv",
                f"{run_slug}__checkpoint_eval_curves.csv"
            ]
            
            has_data = False
            for f in required_files:
                src = ds_root / "tables" / "per_run" / f
                if not src.exists() and "history" in f:
                    src = ds_root / "cache" / "per_run" / run_slug / f
                if not src.exists() and "eval" in f:
                    src = ds_root / "cache" / "per_run" / run_slug / f
                    
                if src.exists():
                    shutil.copy2(src, ds_public / f)
                    has_data = True
            
            if has_data:
                runs_index.append({
                    "dataset": dataset,
                    "run_id": str(row["run_id"]),
                    "run_slug": run_slug,
                    "method": str(row.get("method", "Unknown")),
                    "weather_label": str(row.get("weather_label", "Unknown")),
                    "group_key": str(row.get("group_key", "Unknown")),
                    "primary_metric_value": float(row.get("primary_metric_value", 0.0)) if pd.notna(row.get("primary_metric_value")) else 0.0,
                    "ent_coef": float(row.get("ent_coef", 0.0)) if pd.notna(row.get("ent_coef")) else None,
                    "cost_weight": float(row.get("nutrient_cost_weight", 0.0)) if pd.notna(row.get("nutrient_cost_weight")) else None,
                })

    # Write unified index
    index_path = PUBLIC_DATA_DIR / "runs_index.json"
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(runs_index, f, indent=2)
        
    print(f"Successfully processed {len(runs_index)} runs and copied payloads to public/data.")

if __name__ == "__main__":
    main()
