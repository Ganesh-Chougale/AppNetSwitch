import subprocess

# NOTE: This module expects to be run with root/sudo privileges.

def block_app(pid: int):
    """Adds an iptables rule to drop all OUTPUT traffic from a specific PID."""
    # -m owner --pid-owner: Matches packets owned by the specified PID
    cmd = ["iptables", "-A", "OUTPUT", "-m", "owner", "--pid-owner", str(pid), "-j", "DROP"]
    print("[LINUX] Blocking PID:", " ".join(cmd))
    
    # We must use 'sudo' or rely on the application being run as root
    # Since main.py checks for root, we assume we can call iptables directly.
    try:
        subprocess.run(cmd, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        print(f"[LINUX ERROR] Failed to block PID {pid}. Check root/sudo permissions.")
        print(e.stderr.decode())

def unblock_app(pid: int):
    """Deletes the corresponding iptables rule by PID."""
    # -D OUTPUT: Delete the rule
    cmd = ["iptables", "-D", "OUTPUT", "-m", "owner", "--pid-owner", str(pid), "-j", "DROP"]
    print("[LINUX] Unblocking PID:", " ".join(cmd))

    try:
        subprocess.run(cmd, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        # This often fails if the rule doesn't exist, which is fine.
        if "No such rule" not in e.stderr.decode():
             print(f"[LINUX ERROR] Failed to unblock PID {pid}. Check permissions.")
             print(e.stderr.decode())

# The original get_uid_from_app function is no longer needed and is removed.