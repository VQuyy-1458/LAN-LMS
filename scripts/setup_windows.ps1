$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
py -3.12 -m venv .venv
if ($LASTEXITCODE -ne 0) { throw 'Python 3.12 is required' }
& .\.venv\Scripts\python.exe -m pip install -r server/requirements.lock
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed' }
if (-not (Test-Path server/.env)) { Copy-Item server/.env.example server/.env }
& .\.venv\Scripts\python.exe -m alembic -c server/alembic.ini upgrade head
if ($LASTEXITCODE -ne 0) { throw 'Migration failed' }
