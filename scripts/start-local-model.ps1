# Run from the repository root. Model files and logs stay in ignored .local/.
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $repoRoot
$ollamaBinary = Join-Path $repoRoot '.local\tools\ollama\ollama.exe'
if (-not (Test-Path -LiteralPath $ollamaBinary)) {
    throw 'Local Ollama runtime is missing. Complete the installation in docs/LOCAL_VISION.md.'
}
$env:OLLAMA_HOST = '127.0.0.1:11434'
$env:OLLAMA_MODELS = Join-Path $repoRoot '.local\models'
$env:OLLAMA_NUM_PARALLEL = '1'
$env:OLLAMA_MAX_LOADED_MODELS = '1'
$env:OLLAMA_FLASH_ATTENTION = '1'
$env:OLLAMA_KV_CACHE_TYPE = 'q8_0'
try {
    $null = Invoke-RestMethod 'http://127.0.0.1:11434/api/version' -TimeoutSec 3
    Write-Output 'Local model runtime is already running.'
} catch {
    Start-Process -FilePath $ollamaBinary -ArgumentList 'serve' -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $repoRoot '.local\tools\ollama\server-out.log') `
        -RedirectStandardError (Join-Path $repoRoot '.local\tools\ollama\server-error.log') | Out-Null
    Write-Output 'Started local model runtime. Start the inspection worker separately using docs/LOCAL_VISION.md.'
}
