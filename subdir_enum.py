#!/usr/bin/env python3

import argparse
import subprocess
import os
import sys
from datetime import datetime

### Wordlists
SECLISTS = "/usr/share/seclists"
DIRB = "/usr/share/wordlists/dirb"
WL = {
    "raft_small":   f"{SECLISTS}/Discovery/Web-Content/raft-small-words.txt",
    "raft_medium":  f"{SECLISTS}/Discovery/Web-Content/raft-medium-words.txt",
    "dirb_common":  f"{DIRB}/common.txt",
    "dirb_medium":  f"{SECLISTS}/Discovery/Web-Content/directory-list-2.3-medium.txt",
    "api_objects":  f"{SECLISTS}/Discovery/Web-Content/api/objects.txt",
    "api_actions":  f"{SECLISTS}/Discovery/Web-Content/api/actions.txt",
    "api_leaky":    f"{SECLISTS}/Discovery/Web-Content/api/leaky_paths.txt",
    "graphql":      f"{SECLISTS}/Discovery/Web-Content/graphql.txt",
    "params":       f"{SECLISTS}/Discovery/Web-Content/burp-parameter-names.txt",
}

### Wordlist sets per mode/size
WORDLISTS = {
    "web": {
        "small":  ["dirb_common", "raft_small"],
        "medium": ["dirb_medium", "raft_medium"],
    },
    "api": {
        "small":  ["api_objects", "api_actions", "graphql", "raft_small"],
        "medium": ["api_objects", "api_actions", "api_leaky", "graphql", "raft_medium"],
    },
}


### Helpers
def info(msg):    print(f"[*] {msg}")
def success(msg): print(f"[+] {msg}")
def warn(msg):    print(f"[!] {msg}")
def error(msg):   print(f"[ERROR] {msg}", file=sys.stderr)


def check_tool(name):
    if subprocess.run(["which", name], capture_output=True).returncode != 0:
        error(f"'{name}' not found. Please install it first.")
        sys.exit(1)


def check_wordlist(key):
    path = WL[key]
    if not os.path.isfile(path):
        warn(f"Wordlist not found, skipping: {path}")
        return None
    return path


def run_ffuf(target, wordlist_path, outfile):
    cmd = [
        "ffuf",
        "-u", f"{target}/FUZZ",
        "-w", wordlist_path,
        "-mc", "200,201,204,301,302,307,401,403,405,500",
        "-o", outfile,
        "-of", "csv",
        "-s",           # silent -> no banner, cleaner output
    ]
    info(f"ffuf  →  {wordlist_path}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        warn(f"ffuf exited with code {result.returncode}")


def run_arjun(target, wordlist_path, outfile):
    cmd = [
        "arjun",
        "-u", target,
        "-w", wordlist_path,
        "--output-file", outfile,
        "-c", "5",
    ]
    info(f"arjun →  {wordlist_path}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        warn(f"arjun exited with code {result.returncode}")


def parse_ffuf_csv(filepath):
    """Extract found paths from an ffuf CSV output file."""
    results = {}
    if not os.path.isfile(filepath):
        return results
    with open(filepath) as f:
        for i, line in enumerate(f):
            if i == 0:  # skip header
                continue
            parts = line.strip().split(",")
            if len(parts) >= 4:
                # ffuf CSV: url, redirectlocation, position, status_code, content_length, ...
                url = parts[1].strip().strip('"')
                status_code = parts[4].strip().strip('"')
                if url:
                    results[url] = status_code
    return results


def write_summary(all_paths, outfile):
    sorted_paths = sorted(all_paths.items(), key=lambda x: (min(x[1]), x[0]))

    with open(outfile, "w") as f:
        f.write(f"# subdirectory enumeration summary - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# {len(sorted_paths)} unique paths found\n\n")
        for path, statuses in sorted_paths:
            status_str = "/".join(sorted(statuses))
            flag = "  multiple codes" if len(statuses) > 1 else ""
            f.write(f"{status_str}  {path}{flag}\n")

    success(f"Summary → {outfile}  ({len(sorted_paths)} unique paths)")

def merge_paths(all_paths, new_paths):
    """Merge new_paths dict into all_paths, collecting all status codes per path."""
    for path, status in new_paths.items():
        if path not in all_paths:
            all_paths[path] = {status}
        else:
            all_paths[path].add(status)


### Main
def main():
    parser = argparse.ArgumentParser(
        description="Subdirectory Enumeration Script",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python3 subdir_enum.py -t http://10.10.10.10 --web\n"
            "  python3 subdir_enum.py -t http://10.10.10.10 --api --medium\n"
            "  python3 subdir_enum.py -t http://10.10.10.10 --web --api\n"
            "  python3 subdir_enum.py -t http://10.10.10.10/api/v1/users --param-discovery\n"
        ),
    )
    parser.add_argument("-t", dest="target", required=True, help="Target URL (e.g. http://10.10.10.10)")
    parser.add_argument("--web", action="store_true", help="Standard web directory enumeration")
    parser.add_argument("--api", action="store_true", help="API endpoint enumeration")
    parser.add_argument("--param-discovery", action="store_true", help="HTTP parameter discovery (use full endpoint as -t)")
    parser.add_argument("--medium", action="store_true", help="Use larger wordlists (default: small)")
    args = parser.parse_args()

    if not any([args.web, args.api, args.param_discovery]):
        parser.error("Specify at least one mode: --web, --api, --param-discovery")

    target = args.target.rstrip("/")
    size = "medium" if args.medium else "small"
    outdir = f"./subdirenum_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(outdir)
    info(f"Target : {target}")
    info(f"Mode : {'web ' if args.web else ''}{'api ' if args.api else ''}{'param-discovery' if args.param_discovery else ''}")
    info(f"Size : {size}")
    info(f"Output : {outdir}\n")

    ### Path fuzzing (ffuf)
    all_paths = {}

    if args.web or args.api:
        check_tool("ffuf")
        modes = []
        if args.web: modes.append("web")
        if args.api: modes.append("api")

        for mode in modes:
            for wl_key in WORDLISTS[mode][size]:
                wl_path = check_wordlist(wl_key)
                if not wl_path:
                    continue
                outfile = os.path.join(outdir, f"{mode}_{wl_key}.csv")
                run_ffuf(target, wl_path, outfile)
                merge_paths(all_paths, parse_ffuf_csv(outfile))

        summary_file = os.path.join(outdir, "summary.txt")
        write_summary(all_paths, summary_file)

    ### Parameter discovery (arjun)
    if args.param_discovery:
        check_tool("arjun")
        wl_path = check_wordlist("params")
        if wl_path:
            outfile = os.path.join(outdir, "params.txt")
            run_arjun(target, wl_path, outfile)
            success(f"Arjun results → {outfile}")


if __name__ == "__main__":
    main()