$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
& .\.venv\Scripts\python.exe -m judge.worker @args
exit $LASTEXITCODE
