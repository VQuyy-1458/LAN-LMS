param([switch]$Apply)
$ErrorActionPreference = 'Stop'
$workspace = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..')).TrimEnd('\')
if (-not (Test-Path -LiteralPath (Join-Path $workspace 'client/package.json')) -or
    -not (Test-Path -LiteralPath (Join-Path $workspace 'scripts/launch_web.py'))) {
    throw 'Not a LAN-LMS workspace.'
}

# Keep live data, TLS identity, private account records, one offline kit and audit evidence.
$keepRuntime = @('web', 'launcher', 'tls', 'accounts', 'offline-kit', 'backups', 'audit', 'maintenance', 'bootstrap', 'releases')
$candidates = @('.pytest_cache', 'client/.next/cache', 'output', 'tmp')
Get-ChildItem -LiteralPath (Join-Path $workspace '.runtime') -Force | ForEach-Object {
    $generated = $_.Name -match '^(USB_LAN_LMS_|usb-kit-|offline-check-|docker-repair-backup-20261026-2311$|classroom-2026102[78]$|programming-(20261028|fresh-build-20261028)$|course-transfer-check-20261027$|full-audit-regression$|practical-ui-qa$)' -or
        $_.Name -match '(^|-)tests?(-|$)' -or
        $_.Name -match '^(docker-(probe|curriculum|curriculum-recovered|recovered-tests|live-verification)|repair-wsl-service|update-wsl-|start_project_web\.py)'
    if ($_.Name -notin $keepRuntime -and $generated) { $candidates += '.runtime/' + $_.Name }
}
Get-ChildItem -LiteralPath (Join-Path $workspace '.runtime/backups') -Directory | ForEach-Object {
    if ($_.Name -in @('before-activation-20261028','before-classroom-20261027','before-complete-reset-20261028','before-practical-workflows-20261027','before-student-dob-20261027-final','pre-full-audit-20261026','reset-original-files-20261028')) {
        $candidates += '.runtime/backups/' + $_.Name
    }
}
foreach ($source in @('server', 'judge', 'scripts', 'demo', 'tests', 'experiments', 'database')) {
    Get-ChildItem -LiteralPath (Join-Path $workspace $source) -Directory -Recurse -Force |
        Where-Object Name -eq '__pycache__' | ForEach-Object {
            $candidates += $_.FullName.Substring($workspace.Length + 1)
        }
}

$plan = foreach ($relative in $candidates) {
    $target = [IO.Path]::GetFullPath((Join-Path $workspace $relative))
    if (-not $target.StartsWith($workspace + '\', [StringComparison]::OrdinalIgnoreCase)) {
        throw "Target escapes workspace: $target"
    }
    if (-not (Test-Path -LiteralPath $target)) { continue }
    $item = Get-Item -LiteralPath $target -Force
    $entries = if ($item.PSIsContainer) { @(Get-ChildItem -LiteralPath $target -Recurse -Force) } else { @() }
    if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -or
        @($entries | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint }).Count) {
        throw "Refusing a target containing filesystem links: $target"
    }
    $bytes = if ($item.PSIsContainer) { ($entries | Where-Object { -not $_.PSIsContainer } | Measure-Object Length -Sum).Sum } else { $item.Length }
    [pscustomobject]@{Path=$target; Bytes=[long]$bytes; MiB=[math]::Round($bytes/1MB,2)}
}
$plan | Sort-Object Bytes -Descending | Format-Table Path,MiB -AutoSize | Out-Host
if (-not $Apply) {
    Write-Output 'Preview only. Stop the web, verify the current backup and offline kit, then use -Apply.'
    exit
}
if (-not (Test-Path -LiteralPath (Join-Path $workspace 'tools/nginx/nginx.exe')) -or
    -not (Test-Path -LiteralPath (Join-Path $workspace '.runtime/accounts/LOGIN.txt')) -or
    -not (Test-Path -LiteralPath (Join-Path $workspace '.runtime/offline-kit/manifest.json')) -or
    -not (Test-Path -LiteralPath (Join-Path $workspace '.runtime/backups/current-20261028/manifest.json'))) {
    throw 'Required preserved files are missing. No files removed.'
}
$running = Get-CimInstance Win32_Process | Where-Object {
    $_.Name -in @('python.exe','node.exe','nginx.exe') -and
    $_.CommandLine -like ('*' + $workspace + '*') -and
    $_.CommandLine -match 'uvicorn|judge.worker|next start|nginx.exe'
}
if ($running) { throw 'Project services are still running. Use DUNG_WEB.cmd first.' }
$maintenance = Join-Path $workspace '.runtime/maintenance'
$plan | ConvertTo-Json -Depth 3 | Set-Content -LiteralPath (Join-Path $maintenance 'cleanup-plan.json') -Encoding UTF8
foreach ($entry in $plan) {
    # Every absolute path was checked above and never passed to another shell.
    Remove-Item -LiteralPath $entry.Path -Recurse -Force
}
Write-Output ('Removed {0:N2} GiB of generated files.' -f (($plan | Measure-Object Bytes -Sum).Sum / 1GB))
