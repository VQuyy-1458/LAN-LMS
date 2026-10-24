$ErrorActionPreference = 'Stop'
Set-Location (Join-Path (Split-Path $PSScriptRoot -Parent) 'client')
$manifest = Get-Content -Raw package.json | ConvertFrom-Json
if (-not $manifest.scripts.dev) { throw 'Frontend scaffold only: member 2 must configure dependencies and the dev script first.' }
npm run dev
exit $LASTEXITCODE
