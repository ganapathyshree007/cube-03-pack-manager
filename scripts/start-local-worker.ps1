# Start from any directory after configuring the local .env.
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $repoRoot
& (Join-Path $PSScriptRoot 'start-local-model.ps1')
$env:MODEL_PROVIDER = 'ollama'
$env:OLLAMA_MODEL = 'qwen3-vl:2b-instruct'
$env:MODEL_TIMEOUT_SECONDS = '600'
$env:WORKER_ENABLED = 'true'
$cutoffFile = Join-Path $repoRoot '.local\worker-cutoff.txt'
if (-not (Test-Path -LiteralPath $cutoffFile)) {
    # Exclude historical captures on first activation, including repeated research views.
    [DateTimeOffset]::UtcNow.ToString('o') | Set-Content -LiteralPath $cutoffFile
}
$queueCutoff = (Get-Content -LiteralPath $cutoffFile -Raw).Trim()
Write-Output "Processing new captures queued since $queueCutoff. Keep this worker running for inspections."
& (Join-Path $repoRoot '.venv\Scripts\python.exe') -m backend.worker --created-after $queueCutoff
