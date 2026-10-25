param([switch]$Dev)
$ErrorActionPreference = 'Stop'
Set-Location (Join-Path (Split-Path $PSScriptRoot -Parent) 'client')
if (-not (Test-Path -LiteralPath 'node_modules/next')) { throw 'Run npm ci in client first.' }
if ($Dev) { npm run dev } else {
    if (-not (Test-Path -LiteralPath '.next/BUILD_ID')) { throw 'Run npm run build in client first, or use -Dev.' }
    npm run start
}
exit $LASTEXITCODE
