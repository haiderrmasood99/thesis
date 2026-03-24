$ErrorActionPreference = 'Stop'
$thesisRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $thesisRoot
$pythonCandidates = @(
    'C:\Users\Haider\.conda\envs\cyclesgym\python.exe',
    'C:\ProgramData\anaconda3\python.exe',
    'python'
)
$pythonExe = $pythonCandidates | Where-Object { ($_ -eq 'python') -or (Test-Path $_) } | Select-Object -First 1
if (-not $pythonExe) {
    throw 'No Python interpreter found for smoke runs.'
}

$logDir = Join-Path $thesisRoot 'notes\smoke_runs'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

$commands = @(
    @(
        $pythonExe,
        'experiments/fertilization/train.py',
        '--method','PPO',
        '--total-years','100',
        '--n-process','1',
        '--eval-freq','2000',
        '--seed','0',
        '--nutrient-action-mode','NPK',
        '--price-profile','pakistan_baseline',
        '--maxN','150',
        '--maxP','80',
        '--maxK','60',
        '--p-actions','11',
        '--k-actions','11',
        '--n-nh4-rate','0.75',
        '--fixed-weather',
        '--without-tracking',
        '--summary-json', (Join-Path $logDir 'smoke_fertilization_summary.json')
    ),
    @(
        $pythonExe,
        'experiments/crop_planning/train.py',
        '--method','PPO',
        '--fixed_weather','True',
        '--non_adaptive','False',
        '--seed','0',
        '--price_profile','pakistan_baseline',
        '--without-tracking',
        '--summary-json', (Join-Path $logDir 'smoke_crop_planning_summary.json')
    ),
    @(
        $pythonExe,
        'experiments/crop_planning/train.py',
        '--method','PPO',
        '--fixed_weather','True',
        '--hierarchical','True',
        '--non_adaptive','False',
        '--use_pakistan_crop_calendar','True',
        '--price_profile','pakistan_baseline',
        '--seed','0',
        '--without-tracking',
        '--summary-json', (Join-Path $logDir 'smoke_hierarchical_summary.json')
    )
)

Push-Location $repoRoot
try {
    foreach ($cmd in $commands) {
        Write-Host "Running: $($cmd -join ' ')"
        & $cmd[0] $cmd[1..($cmd.Length-1)]
    }
}
finally {
    Pop-Location
}
