param([int]$Port = 8014, [switch]$CheckOnly, [string]$PostgresBin, [string]$PostgresData)
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $repoRoot
$pythonPath = Join-Path $repoRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) { throw 'Install the documented Python dependencies before offline use.' }
if (-not $PostgresBin) { $PostgresBin = Join-Path $repoRoot '.local\tools\pgsql\bin' }
if (-not $PostgresData) { $PostgresData = Join-Path $repoRoot '.local\pgdata' }
$pgReady = Join-Path $PostgresBin 'pg_isready.exe'
if (Test-Path -LiteralPath $pgReady) {
    & $pgReady -h 127.0.0.1 -p 5432
    if ($LASTEXITCODE -ne 0) {
        $pgControl = Join-Path $PostgresBin 'pg_ctl.exe'
        $pgData = $PostgresData
        if (-not (Test-Path -LiteralPath (Join-Path $pgData 'PG_VERSION'))) { throw 'Existing PostgreSQL cluster not found. No database was created or reset.' }
        & $pgControl -D $pgData -l (Join-Path $repoRoot '.local\postgres.log') start
        if ($LASTEXITCODE -ne 0) { throw 'Local PostgreSQL did not start.' }
    }
}
if ($CheckOnly) { & $pythonPath -m backend.integrated.offline --port $Port --check }
else { & $pythonPath -m backend.integrated.offline --port $Port }
if ($LASTEXITCODE -ne 0) { throw 'Offline launch failed. Existing data was preserved; inspect the error above.' }
