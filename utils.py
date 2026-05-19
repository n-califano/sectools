import subprocess

def run_raw(cmd, timeout=30):
    try:
        output = subprocess.check_output(
            cmd,
            shell=True,
        )
        return output.decode('utf-8', errors='replace').strip()
    except subprocess.CalledProcessError as e:
        return e.output.decode('utf-8', errors='replace').strip()
    except Exception as e:
        return str(e)