# Thesis Dashboard

React/Vite dashboard prototype for exploring thesis experiment outputs.

The app is designed to read generated JSON and CSV payloads from `public/data/`, then display run-level and grouped thesis metrics through interactive charts.

## Run Locally

```bash
npm install
npm run dev
```

Build the production bundle:

```bash
npm run build
npm run preview
```

## Data

Generate dashboard data from the repository root:

```bash
python build_dashboard_data.py
```

By default the script expects a local reporting pack under:

```text
artifacts/final_successful_runs/thesis_reporting_pack/
```

You can override paths with environment variables:

```bash
THESIS_REPO_ROOT=/path/to/thesis THESIS_REPORTING_ROOT=/path/to/thesis_reporting_pack python build_dashboard_data.py
```

On Windows PowerShell:

```powershell
$env:THESIS_REPO_ROOT = "D:\path\to\thesis"
$env:THESIS_REPORTING_ROOT = "D:\path\to\thesis_reporting_pack"
python build_dashboard_data.py
```

Generated files are written to:

```text
thesis_dashboard/public/data/
```

## Notes

- Keep generated dashboard data out of git unless it is intentionally curated for a public demo.
- The dashboard is a thesis visualization surface, not the source of record for final experiment claims.
