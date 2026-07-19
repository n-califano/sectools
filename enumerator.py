import sys
import argparse
import subprocess
import re

### Helpers
def info(msg):    print(f"[*] {msg}")
def success(msg): print(f"[+] {msg}")
def warn(msg):    print(f"[!] {msg}")
def error(msg):   print(f"[ERROR] {msg}", file=sys.stderr)

def print_title(title):
    line = "#" * 60
    print(f"\n{line}")
    print(f"# {title.upper().center(56)} #")
    print(f"{line}\n")

def domain_to_base_dn(domain):
    """Convert sample.com -> DC=sample,DC=com"""
    return ",".join(f"DC={part}" for part in domain.split("."))


def run_cmd(cmd):
    info(f'Running: {" ".join(cmd)}')
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        # Check for common failure indicators
        if result.returncode != 0:
            warn(f"{cmd[0]} exited with code {result.returncode}")
            
        return result
        
    except subprocess.TimeoutExpired:
        warn("Command timed out")
        return None
    except FileNotFoundError:
        warn(f"{cmd[0]} not found in PATH")
        return None


### MSSQL
def clean_mssql_output(output):
    """Remove impacket boilerplate noise, keep only the data."""
    lines = output.splitlines()
    cleaned = []
    
    for line in lines:
        # Skip impacket banner and progress lines
        if line.startswith("Impacket"):
            continue
        if line.startswith("[*]"):
            continue
        if line.startswith("SQL>"):
            continue
        if line.strip() == "" and not cleaned:
            # Skip leading empty lines
            continue
        cleaned.append(line)
    
    return "\n".join(cleaned).strip()


#TODO: currently this method is never called with win_auth=True, consider adding a condition to run it
def run_mssql_command(target_ip, username, password, command, port=1433, win_auth=False):
    cmd = ["impacket-mssqlclient", f"{username}:{password}@{target_ip}", "-p", str(port)]
    
    if win_auth:
        cmd.append("-windows-auth")
    
    cmd.extend(["-command", command])

    result = run_cmd(cmd)
    
    if "Login failed" in result.stderr or "Login failed" in result.stdout:
        warn("Authentication failed")
        
    if "Connection refused" in result.stderr:
        warn("Connection refused - MSSQL may not be running")
        
    return result
    

def enum_databases(target_ip, username, password, port=1433):
    """Enumerate databases using enum_db command."""
    result = run_mssql_command(target_ip, username, password, "enum_db", port)
    if result:
        print("[+] Databases:")
        print(clean_mssql_output(result.stdout) + "\n")


def enum_links(target_ip, username, password, port=1433):
    """Enumerate linked servers."""
    result = run_mssql_command(target_ip, username, password, "enum_links", port)
    if result:
        print("[+] Linked Servers:")
        print(clean_mssql_output(result.stdout) + "\n")


def enum_impersonate(target_ip, username, password, port=1433):
    """Check for impersonation privileges."""
    result = run_mssql_command(target_ip, username, password, "enum_impersonate", port)
    if result:
        print("[+] Impersonation Privileges:")
        print(clean_mssql_output(result.stdout) + "\n")


def enum_logins(target_ip, username, password, port=1433):
    """Enumerate SQL logins and their privileges."""
    result = run_mssql_command(target_ip, username, password, "enum_logins", port)
    if result:
        print("[+] SQL Logins:")
        print(clean_mssql_output(result.stdout) + "\n")

    
def enum_users(target_ip, username, password, port=1433):
    """Enumerate database users."""
    result = run_mssql_command(target_ip, username, password, "enum_users", port)
    if result:
        print("[+] Database Users:")
        print(clean_mssql_output(result.stdout) + "\n")
    

def enum_owners(target_ip, username, password, port=1433):
    """Enumerate database owners."""
    result = run_mssql_command(target_ip, username, password, "enum_owner", port)
    if result:
        print("[+] Database Owners:")
        print(clean_mssql_output(result.stdout) + "\n")


def check_xp_cmdshell(target_ip, username, password, port=1433):
    """
    Check if xp_cmdshell is available (informational only - does not execute).
    This is a configuration check, not an execution.
    """
    result = run_mssql_command(
        target_ip, username, password, 
        "SELECT name, value FROM sys.configurations WHERE name = 'xp_cmdshell'", 
        port
    )
    if result:
        print("[+] xp_cmdshell Configuration:")
        output = clean_mssql_output(result.stdout)
        if output:
            print(output)
            print("    [!] xp_cmdshell procedure exists")
        else:
            print("    xp_cmdshell not found (or no access to sys.objects)")


def run_mssql_check(target_ip, username, password, port=1433):
    """
    Main MSSQL enumeration function.
    """
    print_title("MSSQL Enumeration")
    
    # Test connection first
    info(f"Connecting to {target_ip}:{port} as {username}")
    test = run_mssql_command(target_ip, username, password, "SELECT @@version", port)
    if not test:
        warn("Failed to connect to MSSQL")
        return
    
    # Extract version info from connection output
    version_match = re.search(r'Microsoft SQL Server (\d{4}|\d{2}\.\d)', test.stdout)
    if version_match:
        print(f"[+] MSSQL Version: {version_match.group(1)}\n")
    
    # Run enumeration checks
    enum_databases(target_ip, username, password, port)
    enum_links(target_ip, username, password, port)
    enum_impersonate(target_ip, username, password, port)
    enum_logins(target_ip, username, password, port)
    enum_users(target_ip, username, password, port)
    enum_owners(target_ip, username, password, port)
    
    # Additional security checks
    check_xp_cmdshell(target_ip, username, password, port)
    

### SMB
def parse_smb_shares(result):
    in_shares = False
    shares = []
    for raw in result.splitlines():
        line = raw.rstrip()
        stripped = line.strip()

        if stripped.startswith("Sharename") and "Type" in stripped:
            in_shares = True
            continue
        if in_shares and set(stripped) <= set("-\t "):
            continue
        if not in_shares:
            continue
        # Share rows are indented; footer/status lines are not
        if not line.startswith((" ", "\t")):
            in_shares = False
            continue
        if not stripped:
            in_shares = False
            continue

        parts = stripped.split(None, 2)
        if len(parts) < 2:
            continue
        shares.append(parts[0])

    return shares


def list_smb_shares(target_ip, username, password):
    if username and password:
        cmd = ["smbclient", "-L", f"//{target_ip}", "-U", f"{username}%{password}"]
    else:
        cmd = ["smbclient", "-L", f"//{target_ip}", "-N"]

    result = run_cmd(cmd)
    is_ok = result.returncode == 0 and "NT_STATUS_ACCESS_DENIED" not in result.stderr

    print(result.stdout)

    return result if is_ok else None


def list_smb_share(target_ip, share, username, password):
    # Skip default/admin shares - they either deny anon or just clutter output
    #if share.endswith("$"):
    #    return

    if username and password:
        cmd = ["smbclient", f"//{target_ip}/{share}", "-U", f"{username}%{password}", "-c", "recurse on; dir"]
    else:
        cmd = ["smbclient", f"//{target_ip}/{share}", "-N", "-c", "recurse on; dir"]

    result = run_cmd(cmd)

    if result:
        print(f"[/{share}]")
        print(result.stdout.rstrip()+"\n")


def run_smb_check(target_ip, username, password):
    print_title("SMB Enumeration")

    result = list_smb_shares(target_ip, username, password)

    if result:
        shares = parse_smb_shares(result.stdout)
        for share in shares:
            list_smb_share(target_ip, share, username, password)


### LDAP
def run_ldap_command(target_ip, domain, filter_query, username, password, port=389, use_tls=False):
    base_dn = domain_to_base_dn(domain)

    uri = f"ldaps://{target_ip}" if use_tls else f"ldap://{target_ip}:{port}"

    if username and password:
        cmd = ["ldapsearch", "-x", "-H", uri, "-D", f"{username}@{domain}", 
               "-w", password, "-b", base_dn, filter_query]
    else:
        cmd = ["ldapsearch", "-x", "-H", uri, "-b", base_dn, filter_query]

    if use_tls:
        # Disable certificate verification
        cmd = ["env", "LDAPTLS_REQCERT=never", *cmd]
    
    result = run_cmd(cmd)
        
    if "Can't contact LDAP server" in result.stderr:
        warn("LDAP server not reachable")
            
    return result
        

def enum_ldap_users(target_ip, domain, username, password, port=389):
    """Enumerate LDAP users."""
    result = run_ldap_command(target_ip, domain, "(objectClass=user)", username, password, port)

    if result.returncode == 8: 
        print("[*] Stronger authentication required, trying with ldaps...")
        result = run_ldap_command(target_ip, domain, "(objectClass=user)", username, password, use_tls=True)

    if result:
        print("[+] LDAP Users:")
        print(result.stdout)
        print(result.stderr)


def run_ldap_check(target_ip, domain, username, password, port=389):
    """
    Main LDAP enumeration function.
    """
    print_title("LDAP Enumeration")
    
    info(f"Connecting to ldap://{target_ip}:{port}")
    info(f"Domain: {domain}")
    
    enum_ldap_users(target_ip, domain, username, password, port)


### Users Enumeration
def run_users_enum_check(target_ip, username, password):
    print_title("Users Enumeration")

    cmd = ["rpcclient", "-U", "", "-N", target_ip, "-c", "enumdomusers"]
    result = run_cmd(cmd)
    if result:
        print(result.stdout + "\n")

    if username and password:
        cmd = ["impacket-lookupsid", f"{username}:{password}@{target_ip}"]
        result = run_cmd(cmd)
        if result:  
            print(result.stdout + "\n") 


### AS-REP
def run_asrep_check(target_ip, domain, user=None, user_file=None):
    print_title("AS-REP")

    if user_file:
        cmd = ["impacket-GetNPUsers", f"{domain}/", "-usersfile", user_file, "-dc-ip", target_ip]
    elif user:
        cmd = ["impacket-GetNPUsers", f"{domain}/{user}", "-dc-ip", target_ip, "-no-pass"]

    result = run_cmd(cmd)
    if result:
        print(result.stdout + "\n")


### Password Reuse
def run_password_reuse_check(target_ip, user_list, password_list):
    print_title("Password Reuse")

    #cmd = ["hydra", "-L", user_list, "-P", password_list, "-f", "-V", f"smb2://{target_ip}"]
    cmd = ["netexec", "winrm", target_ip, "-u", user_list, "-p", password_list, "--continue-on-success"]
    
    result = run_cmd(cmd)
    if result:
        for line in result.stdout.splitlines():
            if "[+]" in line:
                # Print only successful attempts
                print(line.strip())


### Active Directory Certificate Services (ADCS)
def run_adcs_check(target_ip, domain, username, password):
    print_title("AD CS Enumeration")

    cmd = ["certipy-ad", "find", "-u", f"{username}@{domain}", "-p", password, "-dc-ip", target_ip, "-vulnerable"]

    result = run_cmd(cmd)
    if result:
        print(result.stdout + result.stderr + "\n")


### Main
def main():
    all_services = ["smb", "mssql", "ldap", "usersenum", "as-rep", "reuse", "adcs"]

    parser = argparse.ArgumentParser(
        description="Enumeration Script",
        formatter_class=argparse.RawTextHelpFormatter,
        #TODO: fix examples
        epilog=(
            "Examples:\n"
            "  python3 subdir_enum.py -t http://10.10.10.10 --web\n"
            "  python3 subdir_enum.py -t http://10.10.10.10 --api --medium\n"
            "  python3 subdir_enum.py -t http://10.10.10.10 --web --api\n"
            "  python3 subdir_enum.py -t http://10.10.10.10/api/v1/users --param-discovery\n"
        ),
    )
    parser.add_argument("-t", dest="target_ip", required=True, help="Target IP (e.g. 10.10.10.10")
    parser.add_argument("-u", dest="username", required=False, help="Username")
    parser.add_argument("-p", dest="password", required=False, help="Password")
    parser.add_argument("-d", dest="domain", required=False, help="Domain")
    parser.add_argument("-U", dest="userfile", required=False, help="Path to a users file, one username per line")
    parser.add_argument("-P", dest="password_file", required=False, help="Path to a passwords file, one password per line")
    parser.add_argument("-s", dest="services", required=False,
                        type=lambda s: [x.strip().lower() for x in s.split(',')],
                        default=all_services,
                        help=f"Services to enumerate (comma-separated, e.g., smb,mssql,ldap). If not specified defaults to all. Possible values: {','.join(all_services)}")

    args = parser.parse_args()

    print(f"Target: {args.target_ip}")

    if "smb" in args.services:
        run_smb_check(args.target_ip, args.username, args.password)

    if "mssql" in args.services:
        if args.username and args.password:
            run_mssql_check(args.target_ip, args.username, args.password)
        else:
            print("[!] Error: need to provide username and password to run mssql check")

    if "ldap" in args.services:
        if args.domain:
            run_ldap_check(args.target_ip, args.domain, args.username, args.password)
        else:
            print("[!] Error: need to provide domain to run ldap check")

    if "usersenum" in args.services:
        run_users_enum_check(args.target_ip, args.username, args.password)

    if "as-rep" in args.services:
        if args.userfile:
            run_asrep_check(args.target_ip, args.domain, user_file=args.userfile)
        elif args.username:
            run_asrep_check(args.target_ip, args.domain, user=args.username)

    if "reuse" in args.services:
        if args.userfile and args.password_file:
            run_password_reuse_check(args.target_ip, args.userfile, args.password_file)
        else:
            print("[!] Error: need to provide a user file and a passwords file to run the password reuse check")

    if "adcs" in args.services:
        if args.domain and args.username and args.password:
            run_adcs_check(args.target_ip, args.domain, args.username, args.password)
        else:
            print("[!] Error: need to provide domain, username and password to run the adcs check")

if __name__ == "__main__":
    main()