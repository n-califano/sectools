import subprocess

def run_raw(cmd: str, timeout: int = 30) -> str:
    """Run a shell command, return raw stdout string. Never raises."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            stdin=subprocess.DEVNULL,
        )
        return result.stdout.strip() + '\n' + result.stderr.strip()
    except Exception:
        return ""