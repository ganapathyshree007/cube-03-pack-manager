$ErrorActionPreference = 'Stop'
if (!(Test-Path .env)) { Copy-Item .env.example .env }
docker compose up --build -d
if ($LASTEXITCODE -ne 0) { throw 'Docker Compose startup failed. Confirm Docker Desktop is running.' }
Write-Output 'Open http://127.0.0.1:8000. Live inference remains pending until Azure is configured.'
