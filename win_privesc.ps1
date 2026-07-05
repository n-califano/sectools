function Write-CustomOutput {
    param(
        [string]$Label,
        [string]$Command,
        [string]$Output
    )
    Write-Host "-> $Label ($Command):"
    Write-Host $Output
    Write-Host ""
}

function Invoke-CmdCommand {
    param(
        [string]$Command,
        [int]$Timeout = 30
    )
    $fullCmd = "cmd /c $Command"
    try {
        $job = Start-Job -ScriptBlock { & $using:fullCmd 2>&1 | Out-String }
        if (Wait-Job $job -Timeout $Timeout) {
            $output = Receive-Job $job
        }
        else {
            Stop-Job $job
            $output = "Command timed out after $Timeout seconds."
        }
        Remove-Job $job -Force
    }
    catch {
        $output = $_.Exception.Message
    }
    return ($output -join "`n").Trim()
}

function Invoke-PSCommand {
    param(
        [string]$Command,
        [int]$Timeout = 30
    )
    try {
        $job = Start-Job -ScriptBlock { Invoke-Expression $using:Command 2>&1 | Out-String }
        if (Wait-Job $job -Timeout $Timeout) {
            $output = Receive-Job $job
        }
        else {
            Stop-Job $job
            $output = "Command timed out after $Timeout seconds."
        }
        Remove-Job $job -Force
    }
    catch {
        $output = $_.Exception.Message
    }
    return ($output -join "`n").Trim()
}

function Build-GitSearchCommand {
    param([string]$Drive = "C:\")
    $blacklist = @(
        "$Drive\Windows",
        "$Drive\Program Files",
        "$Drive\Program Files (x86)",
        "$Drive\ProgramData",
        "$Drive\$Recycle.Bin",
        "$Drive\System Volume Information",
        "$Drive\Recovery",
        "$Drive\Windows.old",
        "$Drive\PerfLogs"
    )

    $usersDir = "$Drive\Users"
    if (Test-Path $usersDir) {
        Get-ChildItem -Path $usersDir -Directory -Force -ErrorAction SilentlyContinue | ForEach-Object {
            $blacklist += Join-Path $_.FullName "AppData"
        }
    }

    # Build PowerShell array literal
    $quotedItems = $blacklist | ForEach-Object { "'$_'" }
    $psArray = $quotedItems -join ","

    $cmd = @"
`$blacklist = @($psArray);
`$roots = Get-ChildItem -Path '$Drive' -Directory -Force -ErrorAction SilentlyContinue | Where-Object { `$blacklist -notcontains `$_.FullName };
foreach (`$root in `$roots) {
    Get-ChildItem -Path `$root.FullName -Directory -Filter '.git' -Recurse -Force -ErrorAction SilentlyContinue
}
"@
    return $cmd
}


function Main {
    $whoami = Invoke-PSCommand "whoami /all"
    Write-CustomOutput "User Information" "whoami /all" $whoami

    $systeminfo = Invoke-PSCommand "systeminfo"
    Write-CustomOutput "System Information" "systeminfo" $systeminfo

    $installed = Invoke-PSCommand 'dir -Path "C:\Program Files", "C:\Program Files (x86)"'
    Write-CustomOutput "Installed Programs" 'dir -Path "C:\Program Files", "C:\Program Files (x86)"' $installed

    $wwwroot = Invoke-PSCommand "dir C:\inetpub\wwwroot"
    if ($wwwroot -like "*File Not Found*") {
        $wwwroot = "Default web root directory not found"
    }
    Write-CustomOutput "Default web root directory for IIS" "dir C:\inetpub\wwwroot" $wwwroot

    $servicesCmd = 'Get-WmiObject win32_service | Where-Object {$_.StartName -notlike "*LocalService*" -and $_.StartName -notlike "*NetworkService*"} | Select Name, DisplayName, PathName, StartName | Format-List | Out-String -Width 500'
    $services = Invoke-PSCommand $servicesCmd
    Write-CustomOutput "Services" $servicesCmd $services

    $envCmd = 'Get-ChildItem Env: | ForEach-Object { "$($_.Name)=$($_.Value)" }'
    $envVars = Invoke-PSCommand $envCmd
    Write-CustomOutput "Environment variables" $envCmd $envVars

    $creds = Invoke-PSCommand "cmdkey /list"
    Write-CustomOutput "Credentials in Windows Credentials Manager" "cmdkey /list" $creds

    $gitCmd = Build-GitSearchCommand
    $gitOutput = Invoke-PSCommand $gitCmd -Timeout 300
    Write-CustomOutput "Git Repositories" $gitCmd $gitOutput

    $oneDrive = Invoke-PSCommand 'dir "$env:OneDrive"'
    Write-CustomOutput "OneDrive" 'dir "$env:OneDrive"' $oneDrive

    Write-Host "Manual Checks:"
    Write-Host '-> SMB (smbclient -L //<TARGET_IP> -U <USER>)'
    Write-Host "Run the smbclient command manually, if you have a valid password for the user"
    Write-Host ""
}

# Run the main function
Main
