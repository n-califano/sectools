# linux_privesc.py

## Checks

| Name | Purpose |
|---------|----------|
| **OS Info** | Distribution and version for known platform exploits |
| **Kernel Version** | Kernel release for known platform exploits |
| **Directories on $PATH** | Writable directories for binary hijacking and PATH injection |
| **SUID/SGID Binaries** | Misconfigured setuid/setgid binaries for privilege escalation |
| **Current user home directory** | SSH keys, configuration files and shell history |
| **/opt directory** | Third-party and custom application installations |
| **Git repos** | Source code repositories potentially containing secrets |
| **Cron Jobs** | Scheduled tasks and writable cron scripts |
| **System timers** | Systemd scheduled timers and persistent units |
| **Running Processes** | Active software and vulnerable running applications |
| **Listening Ports** | Exposed services and internal applications for pivot opportunities |
| **Users** | User accounts and accessible home directories |
| **Sudo Permissions** | Permitted sudo commands for privilege escalation vectors |

## Usage

```bash
python linux_privesc.py
```