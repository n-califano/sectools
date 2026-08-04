# sectools

> A collection of penetration testing and red team utilities for authorized security assessments.

## ⚠️ Disclaimer

**This repository contains tools and scripts intended for authorized security testing, research, and educational purposes only.** 

- Use these tools only on systems you own or have explicit written permission to test
- Unauthorized access to computer systems is illegal under various laws (CFAA, Computer Misuse Act, etc.)
- The authors assume no liability for misuse or damage caused by these tools
- Always obtain proper authorization before using these tools in any environment

## Tools Reference

| Tool | Category | Description | Docs |
|------|----------|-------------|----------|
| `enumerator.py` | Reconnaissance | Multi-service enumerator | [📖 Examples](docs/tools/enumerator.md) |
| `portscan.py` | Reconnaissance | TCP port scanner with service fingerprinting | [📖 Examples](docs/tools/portscan.md) |
| `webenum.py` | Web/Reconnaissance | Directory/file brute-forcer and parameter discovery | [📖 Examples](docs/tools/webenum.md) |
| `blind_sql_extractor.py` | Web/Data Extraction | Blind SQL injection data extractor | [📖 Examples](docs/tools/blind_sql_extractor.md) |
| `linux_privesc.py` | Linux PrivEsc | Automated Linux privilege escalation enumeration | [📖 Examples](docs/tools/linux_privesc.md) |
| `win_privesc.ps1` | Windows PrivEsc | Automated Windows privilege escalation enumeration | [📖 Examples](docs/tools/win_privesc.md) |
| `win_privesc.py` | Windows PrivEsc | Python alternative for Windows privilege escalation (**DEPRECATED**) |  |
| `PSHelpers.psm1` | PS Utils | PowerShell module wrapping complex multi-line operations | [📖 Examples](docs/tools/PSHelpers.md) |


## Prerequisites

### System Requirements

- **Python:** 3.13.14
- **PowerShell:** 5.1.x, 7.6.2
- **Operating System:** Kali Linux 2024.2 and Windows 11

>⚠️ These are the versions used during development: other versions may work but are not guaranteed

### External Tools

These must be installed and available in your `PATH`

| Tool | Version | Required By | 
|------|---------|-------------|
| **impacket** | 0.14.0 | enumerator.py |
| **smbclient** | 4.24.3 | enumerator.py |
| **ldapsearch** | 2.6.10 | enumerator.py |
| **rpcclient** | 4.24.3 | enumerator.py |
| **netexec** | 1.5.1 | enumerator.py |
| **certipy** | 5.1.0 | enumerator.py |
| **nmap** | 7.99 | portscan.py |
| **ffuf** | 2.1.0 | webenum.py |
| **arjun** | 2.2.7 | webenum.py |


>⚠️ These are the versions used during development: other versions may work but are not guaranteed

### Setup

```bash
# Clone the repository
git clone https://github.com/n-califano/sectools.git
cd sectools

# Install Python dependencies
pip install -r requirements.txt
```

## License

This project is licensed under the MIT License.  
See [LICENSE](LICENSE) for the full license text.