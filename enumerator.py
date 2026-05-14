import argparse
import re
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


def main():
    args = parse_args()

    # Basic scan of all tcp ports
    nmap_tcp_sweep_cmd = f"nmap -p- --min-rate 5000 -oN all_tcp_ports.txt {args.target}"
    detected_ports = extract_ports(run_raw(nmap_tcp_sweep_cmd))
    
    # More in-depth scan of detected ports to fingerprint services
    comma_sep_ports = ",".join(str(port) for port in detected_ports)
    nmap_service_scan_cmd = f"nmap -sC -sV -p {comma_sep_ports} -oN service_scan.txt {args.target}"
    print("\n--- Detected services ---")
    print(run_raw(nmap_service_scan_cmd))

    #TODO: consider adding subdirectory enumeration for ports serving websites


if __name__ == "__main__":
    main()