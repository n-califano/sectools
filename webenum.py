#!/usr/bin/env python3

import argparse
import subprocess
import os
import sys
from datetime import datetime
import urllib.request
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

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
    "vhost_small":  f"{SECLISTS}/Discovery/DNS/subdomains-top1million-5000.txt",
    "vhost_medium": f"{SECLISTS}/Discovery/DNS/subdomains-top1million-20000.txt",
    "vhost_large":  f"{SECLISTS}/Discovery/DNS/namelist.txt",
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
        "vhost": {
        "small":  ["vhost_small"],
        "medium": ["vhost_medium"],
        "large":  ["vhost_large"],
    },
}

COMMON_FILES = [
    "robots.txt",
    "sitemap.xml",
    ".git/HEAD",
    ".git/config",
    "security.txt",
    ".well-known/security.txt",
    "crossdomain.xml",
    "clientaccesspolicy.xml",
    "humans.txt",
    "README.md",
    "CHANGELOG.md",
    "LICENSE",
    ".env",
    "config.php",
    "wp-login.php",
    "phpinfo.php",
    ".htaccess",
]

EXTENSION_HINTS = {
    # header name (lowercase) : { substring : [extensions] }
    "x-powered-by": {
        "php":    [".php"],
        "asp":    [".asp", ".aspx"],
        "mono":   [".aspx"],
    },
    "set-cookie": {
        "phpsessid":  [".php"],
        "aspsessionid": [".asp", ".aspx"],
        "jsessionid": [".jsp"],
    },
    "server": {
        "php":    [".php"],
    },
}


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


def run_ffuf(target, wordlist_path, outfile, recursive, extensions=None):
    cmd = [
        "ffuf",
        "-u", f"{target}/FUZZ",
        "-w", wordlist_path,
        "-mc", "200,201,204,301,302,307,401,403,405,500",
        "-o", outfile,
        "-of", "csv",
        "-s",           # silent -> no banner, cleaner output
    ]
    if recursive:
        cmd += ["-recursion", "-recursion-depth", "2"]
    if extensions:
        cmd += ["-e", ",".join(extensions)]
    info(f"Running ffuf cmd  →  {" ".join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        warn(f"ffuf exited with code {result.returncode}")


def run_arjun(target, wordlist_path, outfile, headers=None):
    cmd = [
        "arjun",
        "-u", target,
        "-w", wordlist_path,
        "-oT", outfile,
        "-c", "5",
    ]
    if headers:
        # Arjun expects headers as a single string with \n separators
        header_str = "\n".join(headers)
        cmd.extend(["--headers", header_str])

    info(f"Running arjun cmd  →  {" ".join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        warn(f"arjun exited with code {result.returncode}")

def run_ffuf_vhost(target, domain, wordlist_path, outfile, filter_size=None):
    cmd = [
        "ffuf",
        "-u", target,
        "-H", f"Host: FUZZ.{domain}",
        "-w", wordlist_path,
        "-mc", "200,201,204,301,302,307,401,403,405,500",
        "-o", outfile,
        "-of", "csv",
        "-s",
    ]
    if filter_size is not None:
        cmd += ["-fs", str(filter_size)]
    else:
        warn("No baseline size — vhost results may contain false positives")

    info(f"ffuf vhost enum cmd  →  {cmd}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        warn(f"ffuf vhost exited with code {result.returncode}")

def check_common_files(target):
    info("Checking common files...")
    found = {}
    for path in COMMON_FILES:
        url = f"{target}/{path}"
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=8) as r:
                found[url] = str(r.status)
                success(f"{r.status}  {url}")
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                found[url] = str(e.code)
                #info(f"{e.code}  {url}")
        except Exception:
            pass
    return found

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

def parse_vhost_csv(filepath, domain):
    results = []
    if not os.path.isfile(filepath):
        return results
    with open(filepath) as f:
        for i, line in enumerate(f):
            if i == 0:
                continue
            parts = line.strip().split(",")
            if len(parts) >= 1:
                subdomain = parts[0].strip().strip('"')
                if subdomain:
                    results.append(f"{subdomain}.{domain}")
    return results

def write_summary(all_paths, outfile):
    sorted_paths = sorted(all_paths.items(), key=lambda x: (min(x[1]), x[0]))

    print_title("Summary")

    with open(outfile, "w") as f:
        f.write(f"# subdirectory enumeration summary - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# {len(sorted_paths)} unique paths found\n\n")
        for path, statuses in sorted_paths:
            status_str = "/".join(sorted(statuses))
            flag = "  multiple codes" if len(statuses) > 1 else ""
            line_to_print = f"{status_str}  {path}{flag}"
            f.write(f"{line_to_print}\n")  #write to file
            success(line_to_print)  #write to stdout

    print("")
    success(f"Summary saved to {outfile}  ({len(sorted_paths)} unique paths)")

def merge_paths(all_paths, new_paths):
    """Merge new_paths dict into all_paths, collecting all status codes per path."""
    for path, status in new_paths.items():
        if path not in all_paths:
            all_paths[path] = {status}
        else:
            all_paths[path].add(status)

def get_baseline_size(target, domain):
    """
    Request the target with a garbage Host header to get the
    default response size, used as ffuf -fs filter value.
    This is needed for vhost enumeration: without filtering
    for the default response size it will get a false positive 
    for every word
    """
    try:
        req = urllib.request.Request(target, headers={"Host": f"nonexistent.{domain}"})
        with urllib.request.urlopen(req, timeout=10) as r:
            size = len(r.read())
            info(f"Baseline response size: {size} bytes")
            return size
    except Exception as e:
        warn(f"Could not determine baseline size: {e}")
        return None
    
def detect_extensions(target, extra=None):
    """
    Infer likely extensions from response headers.
    Optionally merge with manually supplied list.
    Returns a deduplicated list of extensions.
    """
    detected = set()

    detected.update(detect_extensions_from_url(target))

    detected.update(detect_extensions_from_header(target))

    if extra:
        manual = {e if e.startswith(".") else f".{e}" for e in extra.split(",")}
        detected.update(manual)
        info(f"Manual extensions added: {manual}")

    if detected:
        success(f"Extensions to fuzz: {sorted(detected)}")
    else:
        info("No extensions detected, fuzzing bare paths only")

    return sorted(detected)

def detect_extensions_from_header(target):
    detected = set()
    try:
        req = urllib.request.Request(target)
        with urllib.request.urlopen(req, timeout=8) as r:
            headers = {k.lower(): v.lower() for k, v in r.headers.items()}
            #info(f"Response headers: {dict(headers)}")  # debug line
            for header, hints in EXTENSION_HINTS.items():
                value = headers.get(header, "")
                for substring, exts in hints.items():
                    if substring in value:
                        detected.update(exts)
                        info(f"Extension hint: '{header}: {value}' → {exts}")
        return detected
    except Exception as e:
        warn(f"Could not detect extensions: {e}")
        return detected

def detect_extensions_from_url(target):
    """Infer extensions by scraping index page links."""
    EXTENSION_IGNORE = {".css", ".js", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".woff", ".woff2", ".ttf"}
    detected = set()
    try:
        req = urllib.request.Request(target)
        with urllib.request.urlopen(req, timeout=8) as r:
            body = r.read().decode("utf-8", errors="ignore")
            import re
            links = re.findall(r'(?:href|src|action)=["\']([^"\'?#]+)', body)
            for link in links:
                _, ext = os.path.splitext(link)
                if ext and len(ext) <= 5 and ext not in EXTENSION_IGNORE:
                    detected.add(ext)
                    #info(f"Extension hint from page link: {ext}")
    except Exception as e:
        warn(f"Could not scrape index for extensions: {e}")
    return detected
    
def enumerate_host(target, label, outdir, args, web_size, api_size):
    """Run requested modes on a single host, writing output to outdir/label/."""
    print_title(f"Enumerating: {label}")
    host_outdir = os.path.join(outdir, label)
    os.makedirs(host_outdir, exist_ok=True)
    all_paths = {}

    merge_paths(all_paths, check_common_files(target)) 
    extensions = detect_extensions(target, extra=args.extensions)

    if args.web or args.api:
        check_tool("ffuf")
        modes = []
        if args.web: modes.append("web")
        if args.api: modes.append("api")
        seen_wordlists = set()
        for mode in modes:
            for wl_key in WORDLISTS[mode][web_size if mode == "web" else api_size]:
                if wl_key in seen_wordlists:
                    info(f"Skipping duplicate wordlist: {wl_key}")
                    continue
                seen_wordlists.add(wl_key)
                wl_path = check_wordlist(wl_key)
                if not wl_path:
                    continue
                outfile = os.path.join(host_outdir, f"{mode}_{wl_key}.csv")
                run_ffuf(target, wl_path, outfile, args.recursive, extensions)
                merge_paths(all_paths, parse_ffuf_csv(outfile))

    all_paths = {k.lower(): all_paths[k] for k in all_paths}    # deduplicate and normalize to lowercase

    if args.param_discovery:
        check_tool("arjun")
        wl_path = check_wordlist("params")
        if wl_path:
            outfile = os.path.join(host_outdir, "params.txt")
            
            for path in all_paths:
                if path.endswith('/'):  # Skip directories
                    continue
                    
                _, ext = os.path.splitext(path)
                if ext and ext.lower() in {e.lower() for e in extensions}:
                    safe_name = path.replace('/', '_').replace('\\', '_')
                    page_outfile = os.path.join(host_outdir, f"params_{safe_name}.txt")
                    run_arjun(path, wl_path, page_outfile, args.headers)

                    # Check if arjun found params (file exists and has content)
                    if os.path.exists(page_outfile) and os.path.getsize(page_outfile) > 0:
                        found_params = True
                        success(f"Arjun found params on {path} → {page_outfile}")

    if all_paths:
        summary_file = os.path.join(host_outdir, "summary.txt")
        write_summary(all_paths, summary_file)

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
    parser.add_argument("--vhost", metavar="DOMAIN", help="Vhost enumeration against base domain (e.g. example.htb)")
    parser.add_argument("--medium", action="store_true", help="Use medium wordlists globally (default: small)")
    parser.add_argument("--web-size", choices=["small", "medium"], default=None)
    parser.add_argument("--api-size", choices=["small", "medium"], default=None)
    parser.add_argument("--vhost-size", choices=["small", "medium", "large"], default=None)
    parser.add_argument("--extensions", metavar="EXT", help="Comma-separated extensions to fuzz (e.g. php,html). Combined with autodetect.", default=None,)
    parser.add_argument("--recursive", action="store_true", help="Recurse into discovered directories")
    parser.add_argument("--headers", dest="headers", required=False,
                        type=lambda s: [x.strip() for x in s.split(',')],
                        help="Specify headers")

    args = parser.parse_args()

    if not any([args.web, args.api, args.param_discovery, args.vhost]):
        parser.error("Specify at least one mode: --web, --api, --param-discovery, --vhost")

    target = args.target.rstrip("/")
    global_size = "medium" if args.medium else "small"
    web_size   = args.web_size   or global_size
    api_size   = args.api_size   or global_size
    vhost_size = args.vhost_size or global_size
    outdir = f"./subdirenum_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(outdir)
    info(f"Target : {target}")
    info(f"Mode : {'web ' if args.web else ''}{'api ' if args.api else ''}{'param-discovery' if args.param_discovery else ''}{'vhost ' if args.vhost else ''}")
    info(f"Size   : web={web_size} api={api_size} vhost={vhost_size}")
    info(f"Output : {outdir}\n")

    vhost_targets = []  # list of (url, label) to enumerate after vhost step

    ### Step 1: vhost enumeration
    if args.vhost:
        check_tool("ffuf")
        wl_key = WORDLISTS["vhost"][vhost_size][0]
        wl_path = check_wordlist(wl_key)
        if wl_path:
            baseline = get_baseline_size(target, args.vhost)
            vhost_csv = os.path.join(outdir, "vhosts.csv")
            run_ffuf_vhost(target, args.vhost, wl_path, vhost_csv, filter_size=baseline)

            discovered = parse_vhost_csv(vhost_csv, args.vhost)

            vhost_summary = os.path.join(outdir, "vhosts.txt")
            with open(vhost_summary, "w") as f:
                f.write(f"# vhosts discovered - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                for h in discovered:
                    f.write(f"{h}\n")
            success(f"Vhosts → {vhost_summary}  ({len(discovered)} found)")

            for vhost in discovered:
                vhost_targets.append((f"http://{vhost}", vhost))

    ### Step 2 — path/param enumeration on base target + discovered vhosts
    if any([args.web, args.api, args.param_discovery]):
        # always include base target
        all_targets = [(target, "base")] + vhost_targets
        for t_url, t_label in all_targets:
            enumerate_host(t_url, t_label, outdir, args, web_size, api_size)

if __name__ == "__main__":
    main()