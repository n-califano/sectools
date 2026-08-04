# enumerator.py

## Available Services

| Service | Flag | Description | Active Directory |
|---------|------|-------------|-------------|
| **[LDAP Users](#ldap-users)** | `-s ldap` | Enumerate user objects | Yes |
| **[AS-REP Roast](#as-rep-roast)** | `-s as-rep` | Find users vulnerable to AS-REP attacks | Yes |
| **[AD CS](#ad-cs)** | `-s adcs` | Check for AD Certificate Services vulnerabilities | Yes |
| **[SMB](#smb)** | `-s smb` | List shares and recursive contents | No |
| **[MSSQL](#mssql)** | `-s mssql` | Run enumeration checks against Microsoft SQL servers | No |
| **[Users Enumeration](#users-enumeration)** | `-s usersenum` | Enumerate system users | No |
| **[Password Spray](#password-spray)** | `-s pwd-spray` | Test user:password combinations | No |

> 💡 **Tip:** Use `-ad` to run all Active Directory checks (LDAP + AS-REP + AD CS) at once.

## Usage Examples

### LDAP Users

<dl>
  <dt>Required</dt>
  <dd><code>-t <TARGET_IP></code>  Target IP address</dd>
  <dd><code>-d <DOMAIN></code>  Active Directory domain</dd>

  <dt>Optional</dt>
  <dd><code>-u <USERNAME></code>  Username</dd>
  <dd><code>-p <PASSWORD></code>  Password</dd>
</dl>

> 💡 **Note:** Anonymous access attempted if credentials omitted.

```bash
# No credentials, anonymous access
python enumerator.py -t <TARGET_IP> -d example.com -s ldap

# With credentials
python enumerator.py -t <TARGET_IP> -d example.com -s ldap -u <USERNAME> -p <PASSWORD>
```

### AS-REP Roast

Identify accounts with "Do not require Kerberos preauthentication" enabled.

<dl>
  <dt>Required</dt>
  <dd><code>-t <TARGET_IP></code>  Target IP address</dd>
  <dd><code>-d <DOMAIN></code>  Active Directory domain</dd>
  <dd><code>-u/-U <USER></code>  Username **OR** Users file</dd>
</dl>


> 💡 **Note:** If both username and users file are provided the check uses the users file and ignores the username

```bash
# Single user
python enumerator.py -t <TARGET_IP> -d example.com -s as-rep -u <USERNAME>

# Bulk check from users list
python enumerator.py -t <TARGET_IP> -d example.com -s as-rep -U <PATH_TO_USERS_LIST>
```

### AD CS

Check for known vulnerabilities in Active Directory Certificate Services

<dl>
  <dt>Required</dt>
  <dd><code>-t <TARGET_IP></code>  Target IP address</dd>
  <dd><code>-d <DOMAIN></code>  Active Directory domain</dd>
  <dd><code>-u <USERNAME></code>  Username</dd>
  <dd><code>-p <PASSWORD></code>  Password</dd>
</dl>

```bash
python enumerator.py -t <TARGET_IP> -d example.com -s adcs -u <USERNAME> -p <PASSWORD>
```

### SMB

List accessible SMB shares and recursively enumerate their contents.

<dl>
  <dt>Required</dt>
  <dd><code>-t <TARGET_IP></code>  Target IP address</dd>

  <dt>Optional</dt>
  <dd><code>-u <USERNAME></code>  Username</dd>
  <dd><code>-p <PASSWORD></code>  Password</dd>
</dl>

> 💡 **Note:** Anonymous access attempted if credentials omitted.

```bash
# Anonymous session
python enumerator.py -t <TARGET_IP> -s smb 

# With credentials
python enumerator.py -t <TARGET_IP> -s smb -u <USERNAME> -p <PASSWORD>
```

### MSSQL

Run common enumeration checks: databases, linked servers, impersonation privileges, logins, db users, db owners and xp_cmdshell availability.

<dl>
  <dt>Required</dt>
  <dd><code>-t <TARGET_IP></code>  Target IP address</dd>
  <dd><code>-u <USERNAME></code>  Username</dd>
  <dd><code>-p <PASSWORD></code>  Password</dd>
</dl>

```bash
python enumerator.py -t <TARGET_IP> -s mssql -u <USERNAME> -p <PASSWORD>
```

### Users Enumeration

Enumerate system users via RPC and SID lookups.

<dl>
  <dt>Required</dt>
  <dd><code>-t <TARGET_IP></code>  Target IP address</dd>

  <dt>Optional</dt>
  <dd><code>-u <USERNAME></code>  Username</dd>
  <dd><code>-p <PASSWORD></code>  Password</dd>
</dl>

> 💡 **Note:** If username and password are not provided only RPC enumeration will be attempted. Otherwise both RPC and SID lookups will be attempted.

```bash
# No credentials, only RPC
python enumerator.py -t <TARGET_IP> -s usersenum

# With credentials, RPC + sid lookups
python enumerator.py -t <TARGET_IP> -s usersenum -u <USERNAME> -p <PASSWORD>
```

### Password Spray

Test credential combinations using WinRM

<dl>
  <dt>Required</dt>
  <dd><code>-t <TARGET_IP></code>  Target IP address</dd>
  <dd><code>-U <USERSFILE></code>  Users file</dd>
  <dd><code>-P <PASSWORDSFILE></code>  Passwords file</dd>
</dl>

```bash
python enumerator.py -t <TARGET_IP> -s pwd-spray -U <PATH_TO_USERS_LIST_FILE> -P <PATH_TO_PASSWORD_LIST_FILE>
```

### Multiple Checks

Multiple checks can be run in bulk by providing a comma separated list to the `-s` parameter.

```bash
# Example: run adcs, smb and userenum checks
python enumerator.py -t <TARGET_IP> -d example.com -s adcs,smb,usersenum -u <USERNAME> -p <PASSWORD>
```

If the `-s` parameter is omitted the program defaults to run all non-AD checks

```bash
# Make sure to provide all required arguments
python enumerator.py -t <TARGET_IP> [OTHER_ARGS]
```

Use the `-ad` switch to run all AD checks in bulk

```bash
# Add all AD checks to the default non-AD checks, thus running all possible checks
python enumerator.py -t <TARGET_IP> -ad [OTHER_ARGS]

# Add all AD checks to the checks specified with the -s parameter
# In this example all AD checks AND the mssql check will be run
python enumerator.py -t <TARGET_IP> -s mssql -u <USERNAME> -p <PASSWORD> -ad <REQUIRED_AD_PARAMS>
```

> 💡 **Note:** When running multiple checks make sure to provide all required arguments