param(
    [ValidateSet('Doctor', 'Prepare', 'Handoff', 'Check', 'Review', 'ReviewCodex', 'AnalyzeAG', 'Implement', 'Status', 'SprintInit', 'SprintRun', 'SprintStatus', 'SprintPacket', 'SprintSync')]
    [string]$Action = 'Doctor',
    [string]$RepoPath = 'C:\Projetos\btg-ai-trader',
    [string]$AgPath = '',
    [string]$PythonPath = '',
    [string]$TaskId = 's8-b01-inventory',
    [string]$Model = '',
    [int]$TimeoutSeconds = 900,
    [switch]$AllowCodex,
    [switch]$AdoptEdits,
    [switch]$SyncGitHub
)

$ErrorActionPreference = 'Stop'
if (-not $AgPath) { $AgPath = Join-Path $env:LOCALAPPDATA 'agy\bin\agy.exe' }
$runner = Join-Path $PSScriptRoot 'agent_workflow.py'
$specPath = Join-Path (Split-Path $PSScriptRoot -Parent) 'config\agent-workflow-s8-inventory.json'
$sprintPath = Join-Path (Split-Path $PSScriptRoot -Parent) 'config\agent-sprint-s8-b01.json'
if (-not (Test-Path -LiteralPath $RepoPath -PathType Container)) {
    throw "Repositório não encontrado: $RepoPath. Informe -RepoPath."
}
if (-not (Test-Path -LiteralPath $AgPath -PathType Leaf)) {
    throw "Antigravity CLI não encontrado: $AgPath. Informe -AgPath."
}
# Only this process gets the CLI directory; no persistent PATH or credentials are changed.
$env:PATH = [IO.Path]::GetDirectoryName($AgPath) + [IO.Path]::PathSeparator + $env:PATH
$env:PYTHONUTF8 = '1'
if (-not $PythonPath) {
    $workflowPython = Join-Path (Split-Path $PSScriptRoot -Parent) '.workflow-venv\Scripts\python.exe'
    $venvPython = Join-Path $RepoPath '.venv\Scripts\python.exe'
    if (Test-Path -LiteralPath $workflowPython -PathType Leaf) {
        $PythonPath = $workflowPython
    } elseif (Test-Path -LiteralPath $venvPython -PathType Leaf) {
        $PythonPath = $venvPython
    } else {
        $PythonPath = (Get-Command python -ErrorAction Stop).Source
    }
}

if ($Action -eq 'Doctor') {
    & $PythonPath $runner --repo $RepoPath doctor
    if ($LASTEXITCODE -ne 0) { throw 'Diagnóstico do coordenador falhou.' }
    & $AgPath --version
    if ($LASTEXITCODE -ne 0) { throw 'Antigravity CLI não iniciou.' }
    & $AgPath models
    if ($LASTEXITCODE -ne 0) {
        throw 'Não foi possível listar os modelos; confira o login interativo em agy.'
    }
    Write-Host 'Use os IDs exatos listados acima. A listagem não comprova cota para geração.'
    exit 0
}

if ($Action.StartsWith('Sprint')) {
    if ($TaskId -eq 's8-b01-inventory') { $TaskId = 's8-b01-sprint-ag' }
    if ($Action -eq 'SprintInit') {
        & $PythonPath $runner --repo $RepoPath sprint init $sprintPath
    } elseif ($Action -eq 'SprintRun') {
        $sprintArgs = @('--repo', $RepoPath, 'sprint', 'run', $TaskId, '--timeout', $TimeoutSeconds)
        if ($AllowCodex) { $sprintArgs += '--allow-codex' }
        if ($AdoptEdits) { $sprintArgs += '--adopt-edits' }
        if ($SyncGitHub) { $sprintArgs += '--sync-github' }
        & $PythonPath $runner @sprintArgs
    } elseif ($Action -eq 'SprintStatus') {
        & $PythonPath $runner --repo $RepoPath sprint status $TaskId
    } elseif ($Action -eq 'SprintPacket') {
        & $PythonPath $runner --repo $RepoPath sprint packet $TaskId
    } else {
        & $PythonPath $runner --repo $RepoPath sprint sync $TaskId
    }
} elseif ($Action -eq 'Prepare') {
    $spec = Get-Content -LiteralPath $specPath -Raw -Encoding UTF8 | ConvertFrom-Json
    & git -C $RepoPath cat-file -e "$($spec.base_sha)^{commit}" 2>$null
    if ($LASTEXITCODE -ne 0) {
        & git -C $RepoPath fetch --no-tags origin 'refs/heads/s8/01-strategy-remediation'
        if ($LASTEXITCODE -ne 0) { throw 'Fetch da branch de remediação falhou.' }
    }
    & $PythonPath $runner --repo $RepoPath prepare $specPath
} elseif ($Action -eq 'Handoff') {
    & $PythonPath $runner --repo $RepoPath export $TaskId
    if ($LASTEXITCODE -eq 0) {
        $handoff = Join-Path $RepoPath "artifacts\agent-workflow\$TaskId\handoff.md"
        Write-Host "Abra no Antigravity o checkout indicado neste pacote: $handoff"
    }
} elseif ($Action -eq 'Check') {
    & $PythonPath $runner --repo $RepoPath check $TaskId --timeout $TimeoutSeconds
} elseif ($Action -eq 'Review') {
    if (-not $Model) { $Model = 'gemini-4-argon-medium' }
    & $PythonPath $runner --repo $RepoPath review $TaskId --provider antigravity --model $Model --timeout $TimeoutSeconds
} elseif ($Action -eq 'ReviewCodex') {
    if (-not $Model) { $Model = 'gpt-6.1-sol' }
    & $PythonPath $runner --repo $RepoPath review $TaskId --provider codex --model $Model --timeout $TimeoutSeconds
} elseif ($Action -eq 'AnalyzeAG') {
    if (-not $Model) { $Model = 'gemini-3.8-flash-medium' }
    & $PythonPath $runner --repo $RepoPath review $TaskId --provider antigravity --model $Model --timeout $TimeoutSeconds
} elseif ($Action -eq 'Implement') {
    if (-not $Model) { $Model = 'claude-sonnet-5-5-medium' }
    & $PythonPath $runner --repo $RepoPath implement $TaskId --model $Model --timeout $TimeoutSeconds
} else {
    & $PythonPath $runner --repo $RepoPath status $TaskId
}
if ($LASTEXITCODE -ne 0) { throw "Etapa $Action bloqueada. Confira o estado e os logs da tarefa." }
