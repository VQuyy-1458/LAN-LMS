param([switch]$CheckOnly, [switch]$LibraryOnly, [switch]$AdminPhase, [switch]$InstallDocker, [switch]$NoOpen)
$ErrorActionPreference = 'Stop'
$project = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..')).TrimEnd('\')
$bootstrap = Join-Path $project '.runtime/bootstrap'
$scriptPath = $PSCommandPath

function ConvertTo-NativeArgument([string]$Value) {
    if ($Value -and $Value -notmatch '[\s"]') { return $Value }
    '"' + ([regex]::Replace($Value, '(\\*)"', '$1$1\"') -replace '(\\+)$', '$1$1') + '"'
}
function Invoke-Native([string]$Exe, [string[]]$Arguments, [int]$Timeout = 30) {
    $info = New-Object Diagnostics.ProcessStartInfo
    $info.FileName = $Exe
    $info.Arguments = ($Arguments | ForEach-Object { ConvertTo-NativeArgument $_ }) -join ' '
    $info.UseShellExecute = $false; $info.CreateNoWindow = $true
    $info.RedirectStandardOutput = $true; $info.RedirectStandardError = $true
    $process = New-Object Diagnostics.Process
    $process.StartInfo = $info
    try {
        [void]$process.Start()
        $stdout = $process.StandardOutput.ReadToEndAsync(); $stderr = $process.StandardError.ReadToEndAsync()
        if (-not $process.WaitForExit($Timeout * 1000)) {
            $process.Kill()
            throw "Lenh qua thoi gian $Timeout giay: $Exe. Khong reset/xoa du lieu; xem Docker/WSL va thu lai."
        }
        [void]$stdout.Wait(1000); [void]$stderr.Wait(1000)
        $text = if ($stdout.IsCompleted) { $stdout.Result } else { '' }
        if ($stderr.IsCompleted) { $text += $stderr.Result }
        [pscustomobject]@{Code=$process.ExitCode; Text=($text -replace "`0", '')}
    } finally { $process.Dispose() }
}
function Invoke-Install([string]$Exe, [string[]]$Arguments, [int]$Timeout = 1800) {
    $logs = Join-Path $bootstrap 'logs'; New-Item -ItemType Directory -Force -Path $logs | Out-Null
    $id = [Guid]::NewGuid().ToString('N')
    $out = Join-Path $logs "$id.out.log"; $err = Join-Path $logs "$id.err.log"
    $argsText = ($Arguments | ForEach-Object { ConvertTo-NativeArgument $_ }) -join ' '
    $proc = Start-Process -FilePath $Exe -ArgumentList $argsText -WorkingDirectory $project -WindowStyle Hidden -PassThru -RedirectStandardOutput $out -RedirectStandardError $err
    $deadline = (Get-Date).AddSeconds($Timeout)
    while (-not $proc.WaitForExit(1000)) {
        if ((Get-Date) -gt $deadline) {
            throw "Qua thoi gian cai dat. Khong tu ket thuc installer he thong. Xem $out va $err; dong installer neu can, roi chay lai file."
        }
    }
    $proc.Refresh(); $code = $proc.ExitCode
    if ($null -eq $code) { throw "Khong doc duoc ket qua installer. Xem $out" }
    if ($code -notin @(0,3010,1641)) {
        $tail = ((Get-Content -LiteralPath $err -Tail 12 -ErrorAction SilentlyContinue) -join "`n")
        throw "Cai dat loi ($code): $Exe. $tail Xem log: $out"
    }
    return [int]$code
}
function Get-Desktop {
    foreach ($folder in @("$env:ProgramFiles\Docker\Docker", "$env:LOCALAPPDATA\Programs\DockerDesktop", "$env:LOCALAPPDATA\Docker\Docker")) {
        $desktop = Join-Path $folder 'Docker Desktop.exe'; $cli = Join-Path $folder 'resources/bin/docker.exe'
        if ((Test-Path -LiteralPath $desktop) -and (Test-Path -LiteralPath $cli)) {
            return [pscustomobject]@{App=$desktop; Cli=$cli}
        }
    }
    return $null
}
function Get-Python {
    $paths = @((Join-Path $bootstrap 'python/python.exe'), (Join-Path $project '.venv/Scripts/python.exe'))
    foreach ($key in @('HKCU:\Software\Python\PythonCore\3.12\InstallPath','HKLM:\Software\Python\PythonCore\3.12\InstallPath')) {
        if (Test-Path $key) {
            $value=(Get-ItemProperty -Path $key).'(default)'
            if ($value) { $paths += Join-Path $value 'python.exe' }
        }
    }
    $py = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($py -and $py.Source -notlike '*WindowsApps*') {
        try { $probe=Invoke-Native $py.Source @('-3.12','-c','import sys;print(sys.executable)'); if ($probe.Code -eq 0) { $paths += $probe.Text.Trim() } } catch {}
    }
    $python = Get-Command python.exe -ErrorAction SilentlyContinue
    if ($python -and $python.Source -notlike '*WindowsApps*') { $paths += $python.Source }
    foreach ($path in $paths) {
        if (-not (Test-Path -LiteralPath $path)) { continue }
        try { $r=Invoke-Native $path @('-c','import sys;print(str(sys.version_info.major)+"."+str(sys.version_info.minor))'); if ($r.Code -eq 0 -and $r.Text.Trim() -eq '3.12') { return $path } } catch {}
    }
    return $null
}
function Get-Node {
    $paths = @((Join-Path $bootstrap 'node/node.exe'))
    $node = Get-Command node.exe -ErrorAction SilentlyContinue
    if ($node) { $paths += $node.Source }
    foreach ($path in $paths) {
        if (Test-Path -LiteralPath $path) { try { $r=Invoke-Native $path @('--version'); if ($r.Code -eq 0 -and $r.Text.Trim() -match '^v24\.') { return $path } } catch {} }
    }
    return $null
}
function Get-WslVersion {
    try {
        $r=Invoke-Native "$env:SystemRoot\System32\wsl.exe" @('--version') 15
        if ($r.Code -eq 0 -and $r.Text -match '(\d+\.\d+\.\d+)') { return [version]$Matches[1] }
    } catch {}
    return [version]'0.0.0'
}
function Get-BootstrapPlan($Facts) {
    if (-not $Facts.Supported) { return @('unsupported') }
    if (-not $Facts.Virtualization) { return @('enable-bios-virtualization') }
    $steps = @()
    if (-not $Facts.Python) { $steps += 'install-python' }
    if (-not $Facts.Node) { $steps += 'install-node' }
    if ([version]$Facts.Wsl -lt [version]'2.1.5') { $steps += 'install-wsl' }
    if (-not $Facts.Docker) { $steps += 'install-docker' }
    if (-not $Facts.Firewall) { $steps += 'configure-private-lan' }
    $steps += @('wait-linux-engine','prepare-app-preserve-data','open-web')
    return $steps
}
function Get-File([string]$Url, [string]$Name, [string]$Publisher = '', [string]$Sha256 = '') {
    $uri=[uri]$Url
    if ($uri.Scheme -ne 'https' -or $uri.Host -notin @('www.python.org','nodejs.org','desktop.docker.com','nginx.org')) { throw 'Nguon tai khong duoc phep' }
    $cache=Join-Path $bootstrap 'downloads'; New-Item -ItemType Directory -Force -Path $cache | Out-Null
    $path=Join-Path $cache $Name
    $valid=$false
    if (Test-Path -LiteralPath $path) {
        $valid=$true
        if ($Sha256 -and (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash -ne $Sha256) { $valid=$false }
        if ($Publisher) { $sig=Get-AuthenticodeSignature -LiteralPath $path; $valid=$sig.Status -eq 'Valid' -and $sig.SignerCertificate.Subject -match $Publisher }
    }
    if (-not $valid) {
        Write-Host "Dang tai $Name tu $($uri.Host)..."
        $partial=if ($Publisher) { $path+'.partial.exe' } else { $path+'.partial' }
        Invoke-WebRequest -UseBasicParsing -Uri $Url -OutFile $partial -TimeoutSec 1800
        if ($Sha256 -and (Get-FileHash -LiteralPath $partial -Algorithm SHA256).Hash -ne $Sha256) { throw "Checksum sai: $Name" }
        if ($Publisher) {
            $sig=Get-AuthenticodeSignature -LiteralPath $partial
            if ($sig.Status -ne 'Valid' -or $sig.SignerCertificate.Subject -notmatch $Publisher) { throw "Chu ky nha phat hanh khong hop le: $Name" }
        }
        Move-Item -LiteralPath $partial -Destination $path -Force
    }
    return $path
}
function Get-ResumeName {
    $sha=[Security.Cryptography.SHA256]::Create()
    try { 'LANLMS-' + ([BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($project))).Replace('-','').Substring(0,12)) } finally { $sha.Dispose() }
}
function Set-Resume {
    $command='powershell.exe -NoProfile -ExecutionPolicy Bypass -File ' + (ConvertTo-NativeArgument $scriptPath)
    if ($NoOpen) { $command += ' -NoOpen' }
    New-Item -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\RunOnce' -Force | Out-Null
    New-ItemProperty -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\RunOnce' -Name (Get-ResumeName) -Value $command -PropertyType String -Force | Out-Null
}
function Clear-Resume {
    Remove-ItemProperty -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\RunOnce' -Name (Get-ResumeName) -ErrorAction SilentlyContinue
}
function Invoke-AdminPhase {
    $principal=New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw 'AdminPhase requires Administrator' }
    $result=@{success=$false; reboot=$false; message=''}
    try {
        foreach ($feature in @('Microsoft-Windows-Subsystem-Linux','VirtualMachinePlatform')) {
            $state=(Get-WindowsOptionalFeature -Online -FeatureName $feature).State
            if ($state -ne 'Enabled') {
                $change=Enable-WindowsOptionalFeature -Online -FeatureName $feature -All -NoRestart
                if ($change.RestartNeeded -or $state -eq 'EnablePending') { $result.reboot=$true }
            }
        }
        if (-not $result.reboot) {
            if ((Get-WslVersion) -lt [version]'2.1.5') {
                $r=Invoke-Native "$env:SystemRoot\System32\wsl.exe" @('--install','--no-distribution','--web-download') 900
                if ($r.Code -notin @(0,3010,1641)) {
                    $r=Invoke-Native "$env:SystemRoot\System32\wsl.exe" @('--update','--web-download') 900
                    if ($r.Code -notin @(0,3010,1641)) { throw "WSL: $($r.Text)" }
                }
                if ($r.Code -in @(3010,1641)) { $result.reboot=$true }
            }
            if ($InstallDocker -and -not (Get-Desktop)) {
                $installer=Get-File 'https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe' 'DockerDesktopInstaller.exe' 'Docker Inc'
                # Do not pass --accept-license: the user accepts in Docker's first-run UI.
                $code=Invoke-Install $installer @('install','--quiet','--backend=wsl-2','--always-run-service','--no-windows-containers')
                if ($code -in @(3010,1641)) { $result.reboot=$true }
            }
        }
        $rule='LANLMS-' + (Get-ResumeName) + '-Private'
        if (-not (Get-NetFirewallRule -Name $rule -ErrorAction SilentlyContinue)) {
            New-NetFirewallRule -Name $rule -DisplayName 'LAN-LMS (Private LAN only)' -Direction Inbound -Action Allow -Program (Join-Path $project 'tools/nginx/nginx.exe') -Protocol TCP -LocalPort 8080,8443 -RemoteAddress LocalSubnet -Profile Private | Out-Null
        }
        $result.success=$true
    } catch { $result.message=$_.Exception.Message }
    $result | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $bootstrap 'admin-result.json') -Encoding UTF8
    if (-not $result.success) { throw $result.message }
}
function Start-Bootstrap {
    if (-not (Test-Path -LiteralPath (Join-Path $project 'client/package.json'))) { throw 'Hay giai nen day du bo project truoc.' }
    $os=Get-CimInstance Win32_OperatingSystem
    $system=Get-CimInstance Win32_ComputerSystem
    $cpu=@(Get-CimInstance Win32_Processor)
    $build=[int]$os.BuildNumber
    $supported=[Environment]::Is64BitOperatingSystem -and ($env:PROCESSOR_ARCHITECTURE -eq 'AMD64' -or $env:PROCESSOR_ARCHITEW6432 -eq 'AMD64') -and ($build -eq 19045 -or $build -ge 22631) -and $os.ProductType -eq 1
    $virtualization=$system.HypervisorPresent -or @($cpu | Where-Object VirtualizationFirmwareEnabled).Count -gt 0
    $desktop=Get-Desktop
    $rule='LANLMS-' + (Get-ResumeName) + '-Private'
    $facts=[pscustomobject]@{Supported=$supported;Virtualization=[bool]$virtualization;MemoryGiB=[math]::Round($system.TotalPhysicalMemory/1GB,1);Python=[bool](Get-Python);Node=[bool](Get-Node);Wsl=(Get-WslVersion).ToString();Docker=[bool]$desktop;Firewall=[bool](Get-NetFirewallRule -Name $rule -ErrorAction SilentlyContinue)}
    $plan=@(Get-BootstrapPlan $facts)
    if ($CheckOnly) { [pscustomobject]@{Facts=$facts;Plan=$plan;Project=$project} | ConvertTo-Json -Depth 4; return }
    if (-not $supported) { throw 'Can Windows x64 10 22H2 (19045) hoac Windows 11 23H2 (22631) tro len. ARM/Windows Server khong duoc bo nay ho tro.' }
    if ($facts.MemoryGiB -lt 8) { throw 'Docker can it nhat 8 GB RAM. Hay dung may khac lam may chu.' }
    if (-not $virtualization) { throw 'Chua bat ao hoa VT-x/AMD-V trong BIOS/UEFI. Bat ao hoa, khoi dong lai va chay lai file nay; script khong tu thay doi BIOS.' }
    New-Item -ItemType Directory -Force -Path $bootstrap | Out-Null
    $lockPath=Join-Path $bootstrap 'setup.lock'
    try { $lock=[IO.File]::Open($lockPath,'OpenOrCreate','ReadWrite','None') } catch { throw 'Bo cai dang chay o cua so khac.' }
    try {
        [Net.ServicePointManager]::SecurityProtocol=[Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
        $env:PYTHONUTF8='1'; $env:DISABLE_SQLALCHEMY_CEXT_RUNTIME='1'
        Write-Host 'LAN-LMS: cai dat va chay. Du lieu da co duoc giu nguyen.'
        if (-not $facts.Python) {
            $installer=Get-File 'https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe' 'python-3.12.10-amd64.exe' 'Python Software Foundation'
            [void](Invoke-Install $installer @('/quiet','InstallAllUsers=0',('TargetDir='+(Join-Path $bootstrap 'python')),'Include_launcher=0','Include_pip=1','Include_test=0','Include_doc=0','Include_tcltk=0','PrependPath=0','Shortcuts=0'))
        }
        if (-not $facts.Node) {
            $version='v24.14.1'
            $kitManifest=Join-Path (Split-Path $project -Parent) 'manifest.json'
            if (Test-Path -LiteralPath $kitManifest) { $version=(Get-Content -LiteralPath $kitManifest -Raw | ConvertFrom-Json).node }
            if ($version -notmatch '^v24\.\d+\.\d+$') { throw 'Node version in kit is invalid' }
            $name="node-$version-win-x64.zip"
            $sums=(Invoke-WebRequest -UseBasicParsing -Uri "https://nodejs.org/dist/$version/SHASUMS256.txt" -TimeoutSec 60).Content
            $match=[regex]::Match($sums,'(?m)^([a-fA-F0-9]{64})\s+'+[regex]::Escape($name)+'\s*$')
            if (-not $match.Success) { throw 'Khong tim thay checksum Node chinh thuc' }
            $zip=Get-File "https://nodejs.org/dist/$version/$name" $name '' $match.Groups[1].Value
            $stage=Join-Path $bootstrap 'node-unpack'; Expand-Archive -LiteralPath $zip -DestinationPath $stage -Force
            if (-not (Test-Path -LiteralPath (Join-Path $bootstrap 'node'))) { Move-Item -LiteralPath (Join-Path $stage "node-$version-win-x64") -Destination (Join-Path $bootstrap 'node') }
        }
        $python=Get-Python; $node=Get-Node
        if (-not $python -or -not $node) { throw 'Chua cai duoc Python 3.12 / Node 24. Xem .runtime/bootstrap/logs.' }
        $env:PATH=(Split-Path $node -Parent)+';'+$env:PATH
        if ('install-wsl' -in $plan -or 'install-docker' -in $plan -or 'configure-private-lan' -in $plan) {
            # One-shot continuation belongs to the original user, not an alternate UAC account.
            Set-Resume
            $resultPath=Join-Path $bootstrap 'admin-result.json'
            if (Test-Path -LiteralPath $resultPath) { Remove-Item -LiteralPath $resultPath }
            $adminArgs='-NoProfile -ExecutionPolicy Bypass -File '+(ConvertTo-NativeArgument $scriptPath)+' -AdminPhase'
            if ('install-docker' -in $plan) { $adminArgs += ' -InstallDocker' }
            $admin=Start-Process powershell.exe -ArgumentList $adminArgs -Verb RunAs -WindowStyle Hidden -PassThru -Wait
            if (-not (Test-Path -LiteralPath $resultPath)) { throw 'Chua duoc cap quyen Administrator. Hay chay lai va bam Yes.' }
            $result=Get-Content -LiteralPath $resultPath -Raw | ConvertFrom-Json
            if (-not $result.success) { throw $result.message }
            if ($result.reboot) {
                Write-Host 'Can khoi dong lai Windows. Da dang ky tiep tuc mot lan sau khi dang nhap. Giu nguyen thu muc nay.'
                if ((Read-Host 'Khoi dong lai ngay? (Y/N)') -match '^[Yy]$') {
                    $shutdown=Invoke-Native "$env:SystemRoot\System32\shutdown.exe" @('/r','/t','15','/c','LAN-LMS: restart Windows to finish WSL setup') 10
                    if ($shutdown.Code -ne 0) { Write-Host 'Hay khoi dong lai Windows bang menu Start. Buoc tiep tuc van duoc giu.' }
                }
                return
            }
        }
        $desktop=Get-Desktop
        if (-not $desktop -or (Get-WslVersion) -lt [version]'2.1.5') { throw 'Docker/WSL chua san sang. Khoi dong lai Windows va chay lai file.' }
        $env:PATH=(Split-Path $desktop.Cli -Parent)+';'+$env:PATH
        Start-Process -FilePath $desktop.App -WindowStyle Hidden
        Write-Host 'Dang cho Docker Linux Engine. Neu Docker hien dieu khoan, hay tu doc va chap nhan de tiep tuc.'
        $deadline=(Get-Date).AddMinutes(8); $ready=$false; $shown=$false
        while ((Get-Date) -lt $deadline) {
            try { $r=Invoke-Native $desktop.Cli @('info','--format','{{.OSType}}') 10; if ($r.Code -eq 0 -and $r.Text.Trim() -eq 'linux') { $ready=$true; break } } catch {}
            if (-not $shown) {
                # The first-run agreement must be visible for the user to review.
                Start-Process -FilePath $desktop.App -WindowStyle Normal
                $shown=$true
            }
            Start-Sleep -Seconds 3
        }
        if (-not $ready) { throw 'Docker Linux Engine chua chay. Mo Docker Desktop, kiem tra dieu khoan/WSL, chon Linux containers roi chay lai. Khong tu reset Docker.' }
        if (-not (Test-Path -LiteralPath (Join-Path $project 'tools/nginx/nginx.exe')) -and -not (Test-Path -LiteralPath (Join-Path (Split-Path $project -Parent) 'dependencies/nginx/nginx.exe'))) {
            $zip=Join-Path $project 'tools/packages/nginx-1.30.6.zip'
            if (-not (Test-Path -LiteralPath $zip)) { $zip=Get-File 'https://nginx.org/download/nginx-1.30.6.zip' 'nginx-1.30.6.zip' }
            $stage=Join-Path $bootstrap 'nginx-unpack'; Expand-Archive -LiteralPath $zip -DestinationPath $stage -Force
            $nginxHash=(Get-FileHash -LiteralPath (Join-Path $stage 'nginx-1.30.6/nginx.exe') -Algorithm SHA256).Hash
            if ($nginxHash -ne 'FB41500AA2508F3D9F791E0888C75CACDBF21CD904826AE42A577E762E5858F5') { throw 'Nginx binary checksum khong dung ban da kiem tra' }
            New-Item -ItemType Directory -Force -Path (Join-Path $project 'tools') | Out-Null
            Copy-Item -LiteralPath (Join-Path $stage 'nginx-1.30.6') -Destination (Join-Path $project 'tools/nginx') -Recurse
        }
        $appArgs=@('-m','scripts.bootstrap_app')
        if ($NoOpen) { $appArgs += '--no-open' }
        & $python @appArgs
        if ($LASTEXITCODE -ne 0) { throw "Buoc chuan bi web bi loi ($LASTEXITCODE). Du lieu cu duoc giu nguyen; xem log va chay lai." }
        Clear-Resume
        Write-Host 'Da hoan tat. Lan sau chi can chay lai CAI_VA_CHAY_LMS.cmd.'
    } catch { Clear-Resume; throw } finally { $lock.Dispose() }
}

if ($LibraryOnly) { return }
try {
    Set-Location -LiteralPath $project
    if ($AdminPhase) {
        New-Item -ItemType Directory -Force -Path $bootstrap | Out-Null
        Invoke-AdminPhase
    } else { Start-Bootstrap }
} catch {
    Write-Host ("LOI: " + $_.Exception.Message) -ForegroundColor Red
    if (-not $CheckOnly -and -not $AdminPhase) { Read-Host 'Nhan Enter de dong, sua theo thong bao roi chay lai cung file' | Out-Null }
    exit 1
}
