import argparse
import re
import sys
import subprocess
from utils import run_raw

def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("--target", required=True, help="Target ip for enumeration")

    return parser.parse_args()

def extract_ports(result):
    # Matches lines like: 80/tcp   open|filtered  http
    pattern = re.compile(r"^(\d+)/(tcp|udp)\s+([\w|]+)\s+(\S+)", re.MULTILINE)

    ports = []
    print(f"--- Detected ports ---")
    for match in pattern.finditer(result):
        port, proto, state, service = match.groups()
        ports.append(int(port))
        print(f"port: {port}; protocol: {proto}; state: {state}")

    return ports

def ping_host(host: str, count: int = 2, timeout: int = 2) -> bool:
    """
    Returns True if host responds to ping.
    Works on Linux/macOS/Windows (with `-n` instead of `-c`).
    """
    param = '-n' if sys.platform.lower().startswith('win') else '-c'
    cmd = ['ping', param, str(count), '-w', str(timeout * 1000), host]
    try:
        result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=timeout + 1)
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        return False


def main():
    args = parse_args()

    # Check basic connectivity
    if not ping_host(args.target):
        print(f"Target {args.target} not reachable via ICMP. "
              "Either you are not on the same subnet or the target blocks ICMP packets")

    # Basic scan of all tcp ports
    nmap_tcp_sweep_cmd = f"nmap -p- --min-rate 5000 -oN all_tcp_ports.txt {args.target}"
    detected_ports = extract_ports(run_raw(nmap_tcp_sweep_cmd))
    
    if detected_ports:
        # More in-depth scan of detected ports to fingerprint services
        comma_sep_ports = ",".join(str(port) for port in detected_ports)
        nmap_service_scan_cmd = f"nmap -sC -sV -p {comma_sep_ports} -oN service_scan.txt {args.target}"
        print("\n--- Detected services ---")
        print(run_raw(nmap_service_scan_cmd))
    else:
        print("General scan did not reveal any port, skipping in-depth scan. Nothing more to do.")


if __name__ == "__main__":
    main()