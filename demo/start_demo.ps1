$ErrorActionPreference = "Stop"

Set-Location -Path (Join-Path $PSScriptRoot "..")
python -m streamlit run demo/app.py
