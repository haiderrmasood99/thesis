$ErrorActionPreference = 'Stop'
$thesisRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent (Split-Path -Parent $thesisRoot)
$localTectonic = Join-Path $repoRoot '.tools\tectonic\tectonic.exe'
$tectonic = $null
if (Test-Path $localTectonic) {
    $tectonic = $localTectonic
}
else {
    $tectonicCmd = Get-Command tectonic -ErrorAction SilentlyContinue
    if ($tectonicCmd) {
        $tectonic = $tectonicCmd.Source
    }
}
if (-not $tectonic) {
    throw "Tectonic binary not found at $localTectonic and not available on PATH."
}
Push-Location $thesisRoot
try {
    python .\scripts\build_assets.py
    & $tectonic -X compile --keep-logs --keep-intermediates --outdir build main.tex
}
finally {
    Pop-Location
}
