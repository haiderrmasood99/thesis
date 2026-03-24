$ErrorActionPreference = 'Stop'
$thesisRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $thesisRoot
$tectonic = Join-Path $repoRoot '.tools\tectonic\tectonic.exe'
if (-not (Test-Path $tectonic)) {
    throw "Tectonic binary not found at $tectonic"
}
Push-Location $thesisRoot
try {
    python .\scripts\build_assets.py
    & $tectonic -X compile --keep-logs --keep-intermediates --outdir build main.tex
}
finally {
    Pop-Location
}
