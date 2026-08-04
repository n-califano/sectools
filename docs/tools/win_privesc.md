# win_privesc.ps1

## Checks

| Name | Purpose |
|---------|----------|
| **User Information** | Current user, privileges, groups, and token details |
| **System Information** | OS version, architecture, and installed hotfixes |
| **Installed Programs** | Program directories for vulnerable software enumeration |
| **IIS** | Web server document roots and virtual directories |
| **Services** | Non-standard service accounts and binary paths | 
| **Environment Variables** | Hardcoded credentials, API keys, and sensitive configuration leaks |
| **Cached Credentials** | Stored credentials in Windows Credential Manager for lateral movement |
| **Git Repositories** | Source code repositories potentially containing secrets and config files |
| **OneDrive** | Cloud-synchronized files and personal document stores |
| **Listening Ports** | Exposed services and internal applications for pivot opportunities |
| **Running Processes** | Active software, vulnerable applications, and security tools (AV/EDR) |
| **Domain Groups** | Active Directory group memberships and privilege targets |

## Usage

```powershell
.\win_privesc.ps1
```