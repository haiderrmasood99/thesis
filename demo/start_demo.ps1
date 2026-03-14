$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path $scriptRoot -Parent
$backendRoot = Join-Path $scriptRoot "backend"
$frontendRoot = Join-Path $scriptRoot "frontend"

$backendCommand = "Set-Location '$backendRoot'; python run_local.py"
$frontendCommand = "Set-Location '$frontendRoot'; npm run dev -- --host 127.0.0.1 --port 5173"

Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCommand
Start-Sleep -Seconds 2
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCommand

Write-Host "Backend starting on http://127.0.0.1:8000"
Write-Host "Frontend starting on http://127.0.0.1:5173"
