from utils import run_raw
import sys

def custom_print(label, cmd, output):
    print('-> {} ({}):\n{}\n'.format(label, cmd, output))
    sys.stdout.flush()

def main():
    os_rel_cmd = "cat /etc/os-release"
    custom_print("OS Info", os_rel_cmd, run_raw(os_rel_cmd))

    uname_cmd = "uname -a"
    custom_print("Kernel Version", uname_cmd, run_raw(uname_cmd))

    dirs_on_PATH_cmd = 'for d in $(echo $PATH | tr ":" " "); do ls -ld "$d"; done'
    custom_print("Directories on $PATH", dirs_on_PATH_cmd, run_raw(dirs_on_PATH_cmd))

    suid_sgid_cmd = 'find / -perm -u=s -type f 2>/dev/null'
    custom_print("SUID/SGID Binaries", suid_sgid_cmd, run_raw(suid_sgid_cmd))

    user_dir = run_raw('grep "^$(whoami):" /etc/passwd | cut -d: -f6')
    ls_home_cmd = 'ls -la {}'.format(user_dir)
    custom_print("Current user home directory", ls_home_cmd, run_raw(ls_home_cmd))

    ls_opt_cmd = 'ls -la /opt'
    custom_print("/opt directory", ls_opt_cmd, run_raw(ls_opt_cmd))

    find_git_repos_cmd = 'find / -name ".git" -type d 2>/dev/null'
    custom_print("Git repos", find_git_repos_cmd, run_raw(find_git_repos_cmd))

    cron1_cmd = 'crontab -l'
    custom_print(cron1_cmd, cron1_cmd, run_raw(cron1_cmd))

    cron2_cmd = 'cat /etc/crontab'
    custom_print(cron2_cmd, cron2_cmd, run_raw(cron2_cmd))

    cron3_cmd = 'ls -la /etc/cron.*'
    custom_print(cron3_cmd, cron3_cmd, run_raw(cron3_cmd))

    timers_cmd = 'systemctl list-timers --all'
    custom_print('System timers', timers_cmd, run_raw(timers_cmd))

    processes_cmd = 'ps aux'
    custom_print('Running processes', processes_cmd, run_raw(processes_cmd))

    listening_ports_cmd = 'ss -tlnp'
    custom_print('Listening ports', listening_ports_cmd, run_raw(listening_ports_cmd))

    sudo_perm_cmd = 'sudo -n -l'
    custom_print("Sudo Permissions", sudo_perm_cmd, run_raw(sudo_perm_cmd, timeout=3))


if __name__ == "__main__":
    main()