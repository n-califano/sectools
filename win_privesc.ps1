function Write-CustomOutput {
    param([string]$Label, [string]$Command, [string]$Output)
    
    $line = "#" * 60
    $title = "$Label".ToUpper()
    $centered = $title.PadLeft($title.Length + (56 - $title.Length) / 2).PadRight(56)
    
    Write-Host "`n$line`n# $centered #`n$line`n"
    Write-Host "Command: $Command"
    Write-Host ""
    Write-Host $Output
    Write-Host ""
}

function Invoke-CmdCommand {
    param(
        [string]$Command,
        [int]$Timeout = 30
    )
    
    $tempOut = [System.IO.Path]::GetTempFileName()
    $tempErr = [System.IO.Path]::GetTempFileName()
    
    try {
        $psi = New-Object System.Diagnostics.ProcessStartInfo
        $psi.FileName = "cmd.exe"
        $psi.Arguments = "/c $Command"
        $psi.RedirectStandardOutput = $true
        $psi.RedirectStandardError = $true
        $psi.UseShellExecute = $false
        $psi.CreateNoWindow = $true
        
        $process = New-Object System.Diagnostics.Process
        $process.StartInfo = $psi
        $process.Start() | Out-Null
        
        # Async read to prevent deadlocks on large output
        $stdout = $process.StandardOutput.ReadToEndAsync()
        $stderr = $process.StandardError.ReadToEndAsync()
        
        if ($process.WaitForExit($Timeout * 1000)) {
            $output = $stdout.Result
            $errorOutput = $stderr.Result
            
            if ($process.ExitCode -ne 0 -and $errorOutput) {
                $output = "EXIT CODE $($process.ExitCode): $errorOutput`n$output"
            }
        }
        else {
            $process.Kill()
            $output = "Command timed out after $Timeout seconds."
        }
        
        $process.Dispose()
    }
    catch {
        $output = $_.Exception.Message
    }
    finally {
        if (Test-Path $tempOut) { Remove-Item $tempOut -ErrorAction SilentlyContinue }
        if (Test-Path $tempErr) { Remove-Item $tempErr -ErrorAction SilentlyContinue }
    }
    
    return $output.Trim()
}

function Invoke-PSCommand {
    param(
        [string]$Command,
        [int]$Timeout = 30
    )
    
    # Encode command to avoid escaping issues and CLM restrictions on complex args
    $wrappedCommand = "`$ProgressPreference='SilentlyContinue'; $Command"   # Silence progress to avoid it leaking into stderr (CLIXML)
    $bytes = [System.Text.Encoding]::Unicode.GetBytes($wrappedCommand)
    $encodedCommand = [Convert]::ToBase64String($bytes)
    
    try {
        $psi = New-Object System.Diagnostics.ProcessStartInfo
        $psi.FileName = "powershell.exe"
        $psi.Arguments = "-EncodedCommand $encodedCommand -NoProfile -ExecutionPolicy Bypass"
        $psi.RedirectStandardOutput = $true
        $psi.RedirectStandardError = $true
        $psi.UseShellExecute = $false
        $psi.CreateNoWindow = $true
        
        $process = New-Object System.Diagnostics.Process
        $process.StartInfo = $psi
        $process.Start() | Out-Null
        
        $stdout = $process.StandardOutput.ReadToEndAsync()
        $stderr = $process.StandardError.ReadToEndAsync()
        
        if ($process.WaitForExit($Timeout * 1000)) {
            $output = $stdout.Result
            $errorOutput = $stderr.Result
            
            if ($errorOutput) {
                $output = "ERROR: $errorOutput`n$output"
            }
        }
        else {
            $process.Kill()
            $output = "Command timed out after $Timeout seconds."
        }
        
        $process.Dispose()
    }
    catch {
        $output = $_.Exception.Message
    }
    
    return $output.Trim()
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

function Get-Services {
    # Try 1: Get-CimInstance
    $ScriptBlock = {
        $ErrorActionPreference = 'SilentlyContinue'
        Get-CimInstance Win32_Service | 
        Where-Object {$_.StartName -notmatch "LocalService|NetworkService|LocalSystem"} | 
        Select-Object Name, DisplayName, PathName, StartName | 
        Format-List | 
        Out-String -Width 500
    }
    $services = & $ScriptBlock 2>$null
    
    if ($services) {
        $cmd = $ScriptBlock.ToString().Trim()
        Write-CustomOutput "Services" $cmd $services
        return
    }
    
    # Try 2: Get-WmiObject
    $ScriptBlock = {
        $ErrorActionPreference = 'SilentlyContinue'
        Get-WmiObject win32_service | 
        Where-Object {$_.StartName -notmatch "LocalService|NetworkService"} | 
        Select-Object Name, DisplayName, PathName, StartName | 
        Format-List | 
        Out-String -Width 500
    }
    $services = & $ScriptBlock 2>$null
    
    if ($services) {
        $cmd = $ScriptBlock.ToString().Trim()
        Write-CustomOutput "Services" $cmd $services
        return
    }
    
    # Try 3: sc.exe
    $ScriptBlock = {
        $ErrorActionPreference = 'SilentlyContinue'
        sc.exe query type= service state= all
    }
    $services = & $ScriptBlock 2>$null | Out-String
    
    if ($LASTEXITCODE -eq 0 -and $services -notmatch "FAILED|Access is denied") {
        Write-CustomOutput "Services" $ScriptBlock.ToString().Trim() $services
        return
    }
    
    # Try 4: Registry
    $ScriptBlock = {
        $ErrorActionPreference = 'SilentlyContinue'
        Get-ChildItem HKLM:\SYSTEM\CurrentControlSet\Services | 
        Get-ItemProperty | 
        Select-Object PSChildName, ImagePath, ObjectName | 
        Format-List | 
        Out-String -Width 500
    }
    $services = & $ScriptBlock 2>$null
    
    if ($services) {
        $cmd = $ScriptBlock.ToString().Trim()
        Write-CustomOutput "Services" $cmd $services
    } else {
        Write-CustomOutput "Services" "All methods failed" "Unable to retrieve services"
    }
}

function Get-IISDir {
    $path = "C:\inetpub\wwwroot"
    $checkCmd = "Test-Path $path"
    $pathExists = Invoke-PSCommand $checkCmd

    if ($pathExists -like "*True*") {
        $wwwroot = Invoke-PSCommand "dir $path"
    } else {
        $wwwroot = "Default web root directory not found"
    }
    Write-CustomOutput "Default web root directory for IIS" "dir $path" $wwwroot
}

function Invoke-SystemCheck {
    param(
        [string]$Label,
        [scriptblock]$ScriptBlock
    )

    $commandString = $ScriptBlock.ToString().Trim()
    
    try {
        $output = & $ScriptBlock 2>&1 | Out-String
        
        if ($LASTEXITCODE -ne 0) {
            Write-CustomOutput $Label $commandString $output
        }
        else {
            Write-CustomOutput $Label $commandString $output
        }
    }
    catch {
        Write-CustomOutput $Label $commandString "EXCEPTION: $($_.Exception.Message)"
    }
}

function Get-OneDrive {
    $ScriptBlock = {Get-ChildItem $env:OneDrive | Out-String}

    if (-not $env:OneDrive) {
        Write-CustomOutput "OneDrive" $ScriptBlock.ToString().Trim() "OneDrive not configured for this user"
        return
    }
    
    if (Test-Path $env:OneDrive) {
        $output = & $ScriptBlock
        Write-CustomOutput "OneDrive" $ScriptBlock.ToString().Trim() $output
    } else {
        Write-CustomOutput "OneDrive" $ScriptBlock.ToString().Trim() "OneDrive path does not exist"
    }
}

#TODO: Invoke-PSCommand is to be considered as deprecated and should be gradually replaced
function Main {
    $whoami = Invoke-PSCommand "whoami /all"
    Write-CustomOutput "User Information" "whoami /all" $whoami

    Invoke-SystemCheck "System Information" { systeminfo }

    Invoke-SystemCheck "Installed Programs" { Get-ChildItem "C:\", "C:\Program Files", "C:\Program Files (x86)" }

    Get-IISDir

    Get-Services

    $envCmd = 'Get-ChildItem Env: | ForEach-Object { "$($_.Name)=$($_.Value)" }'
    $envVars = Invoke-PSCommand $envCmd
    Write-CustomOutput "Environment variables" $envCmd $envVars

    $creds = Invoke-PSCommand "cmdkey /list"
    Write-CustomOutput "Credentials in Windows Credentials Manager" "cmdkey /list" $creds

    $gitCmd = Build-GitSearchCommand
    #$gitOutput = Invoke-PSCommand $gitCmd -Timeout 300
    Write-CustomOutput "Git Repositories" $gitCmd $gitOutput

    Get-OneDrive

    $netstat = Invoke-PSCommand 'netstat -ano'
    Write-CustomOutput "Listening Ports" 'netstat -ano' $netstat

    $ps = Invoke-PSCommand 'ps'
    Write-CustomOutput "Processes" 'ps' $ps

    Write-Host "Manual Checks:"
    Write-Host '-> SMB (smbclient -L //<TARGET_IP> -U <USER>)'
    Write-Host "Run the smbclient command manually, if you have a valid password for the user"
    Write-Host ""
}

# Run the main function
Main
