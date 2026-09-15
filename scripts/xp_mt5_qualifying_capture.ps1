param(
    [string]$Instrument = "WINV26",
    [int]$CaptureSeconds = 120
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$env:PYTHONPATH = Join-Path $repoRoot "src"

python (Join-Path $PSScriptRoot "xp_mt5_qualifying_capture.py") `
    --instrument $Instrument `
    --capture-seconds $CaptureSeconds

exit $LASTEXITCODE
