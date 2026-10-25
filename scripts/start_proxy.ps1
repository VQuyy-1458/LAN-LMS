param([Parameter(Mandatory=$true)][string]$NginxPath)
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path $PSScriptRoot -Parent
$configPath = Join-Path $PSScriptRoot 'nginx.conf'
$runtimePath = Join-Path $repoRoot '.runtime/nginx'
New-Item -ItemType Directory -Force (Join-Path $runtimePath 'logs'),(Join-Path $runtimePath 'temp') | Out-Null
$nginxExe = (Resolve-Path -LiteralPath $NginxPath).Path
$prefix = $runtimePath.Replace('\', '/') + '/'
& $nginxExe -p $prefix -c $configPath -t
if ($LASTEXITCODE -ne 0) { throw 'Nginx configuration check failed; proxy was not started.' }
# Foreground in this terminal; no separate visible helper window.
& $nginxExe -p $prefix -c $configPath -g 'daemon off;'
exit $LASTEXITCODE
