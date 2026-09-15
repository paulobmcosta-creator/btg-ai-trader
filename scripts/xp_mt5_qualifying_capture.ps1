param(
    [string]$Instrument = "WINV26"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Write-Host "BTG Sprint 1 passive capture launcher"
Write-Host "Instrument: $Instrument"
Write-Host "Repository: $repoRoot"
