import sys
import subprocess
import os

def run_raw(cmd, timeout=30):
    try:
        output = subprocess.check_output(
            cmd,
            shell=True,
            stderr=subprocess.STDOUT,
        )
        return output.decode('utf-8', errors='replace').strip()
    except subprocess.CalledProcessError as e:
        return e.output.decode('utf-8', errors='replace').strip()
    except Exception as e:
        return str(e)
    
def run_ps(cmd, timeout=30):
    full_cmd = ["powershell", "-NoProfile", "-Command", f"{cmd}"]
    try:
        output = subprocess.check_output(
            full_cmd,
            stderr=subprocess.STDOUT,
            timeout=timeout,
        )
        return output.decode('utf-8', errors='replace').strip()
    except subprocess.CalledProcessError as e:
        return e.output.decode('utf-8', errors='replace').strip()
    except Exception as e:
        return str(e)
    
def custom_print(label, cmd, output):
    print('-> {} ({}):\n{}\n'.format(label, cmd, output))
    sys.stdout.flush()

def build_git_search_cmd(drive="C:\\"):
    # Static top-level folders to skip
    blacklist = [
        os.path.join(drive, "Windows"),
        os.path.join(drive, "Program Files"),
        os.path.join(drive, "Program Files (x86)"),
        os.path.join(drive, "ProgramData"),
        os.path.join(drive, "$Recycle.Bin"),
        os.path.join(drive, "System Volume Information"),
        os.path.join(drive, "Recovery"),
        os.path.join(drive, "Windows.old"),
        os.path.join(drive, "PerfLogs"),
    ]

    # Add AppData for every user under C:\Users
    users_dir = os.path.join(drive, "Users")
    if os.path.isdir(users_dir):
        for entry in os.scandir(users_dir):
            if entry.is_dir():
                blacklist.append(os.path.join(entry.path, "AppData"))

    # Format as a PowerShell array literal: @('C:\Windows','C:\Users\bob\AppData',...)
    ps_array = ",".join(f"'{p}'" for p in blacklist)

    list_git_repos_cmd = (
        f"$blacklist = @({ps_array}); "
        f"$roots = Get-ChildItem -Path '{drive}' -Directory -Force -ErrorAction SilentlyContinue "
        f"| Where-Object {{ $blacklist -notcontains $_.FullName }}; "
        f"foreach ($root in $roots) {{ "
        f"Get-ChildItem -Path $root.FullName -Directory -Filter '.git' -Recurse -Force -ErrorAction SilentlyContinue "
        f"}}"
    )

    return list_git_repos_cmd

def main():
    whoami_cmd = "whoami /all"
    custom_print("User Information", whoami_cmd, run_raw(whoami_cmd))

    systeminfo_cmd = "systeminfo"
    custom_print("System Information", systeminfo_cmd, run_raw(systeminfo_cmd))

    installed_progs_cmd = r'dir "C:\Program Files" "C:\Program Files (x86)"'
    custom_print("Installed Programs", installed_progs_cmd, run_raw(installed_progs_cmd))

    list_default_iis_dir_cmd = r"dir C:\inetpub\wwwroot"
    wwwroot_dir = run_raw(list_default_iis_dir_cmd)
    wwwroot_dir_output = "Default web root directory not found" if "File Not Found" in wwwroot_dir else wwwroot_dir
    custom_print("Default web root directory for IIS", list_default_iis_dir_cmd, wwwroot_dir_output)

    list_services_cmd = 'Get-WmiObject win32_service | Where-Object {$_.StartName -notlike "*LocalService*" -and $_.StartName -notlike "*NetworkService*"} | Select Name, DisplayName, PathName, StartName | Format-List | Out-String -Width 500'
    custom_print("Services", list_services_cmd, run_ps(list_services_cmd))

    env_cmd = 'Get-ChildItem Env: | ForEach-Object { "$($_.Name)=$($_.Value)" }'
    custom_print("Environment variables", env_cmd, run_ps(env_cmd))

    list_creds_cmd = r"cmdkey /list"
    custom_print("Credentials in Windows Credentials Manager", list_creds_cmd, run_raw(list_creds_cmd))

    list_git_repos_cmd = build_git_search_cmd()
    custom_print("Git Repositories", list_git_repos_cmd, run_ps(list_git_repos_cmd, timeout=300))

    list_onedrive_cmd = 'dir "%OneDrive%"'
    custom_print("OneDrive", list_onedrive_cmd, run_raw(list_onedrive_cmd))

    print("Manual Checks:")
    print('-> SMB (smbclient -L //<TARGET_IP> -U <USER>)')
    print("Run the smbclient command manually, if you have a valid password for the user\n")

if __name__ == "__main__":
    main()