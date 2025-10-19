import subprocess
import ctypes
import os

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_cmd(cmd):
    """Runs netsh command and prints relevant output/errors."""
    try:
        # Use shell=False for security if possible, but netsh often requires it or complex escaping
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True, timeout=10)
        if result.stdout:
            print(f"[netsh stdout] {result.stdout.strip()}")
        if result.stderr and "No rules match the specified criteria" not in result.stderr:
            print(f"[netsh stderr] {result.stderr.strip()}")
        return result.stdout
    except subprocess.TimeoutExpired:
        print(f"[ERROR] Command timed out: {cmd}")
    except Exception as e:
        print(f"[ERROR] {e}")

def format_rule_name(app_path: str) -> str:
    """Creates a unique and sanitized rule name from the application path."""
    # Use part of the path hash to ensure uniqueness even if names collide
    path_hash = str(abs(hash(app_path)))[:8]
    exe_name = os.path.basename(app_path).replace('.', '_')
    return f"AppNetSwitch_{exe_name}_{path_hash}"

def block_app(app_path: str):
    """Adds a persistent outbound block rule by path."""
    rule_name = format_rule_name(app_path)
    print(f"[WINDOWS] Blocking app: {app_path} (rule name: {rule_name})")
    
    # Block Outbound traffic (most critical)
    cmd = (
        f'netsh advfirewall firewall add rule name="{rule_name}" '
        f'dir=out action=block program="{app_path}" enable=yes'
    )
    run_cmd(cmd)

def unblock_app(app_path: str):
    """Deletes the block rule by its unique name."""
    rule_name = format_rule_name(app_path)
    print(f"[WINDOWS] Unblocking app: {app_path} (rule name: {rule_name})")
    
    # Delete rule by unique name
    run_cmd(f'netsh advfirewall firewall delete rule name="{rule_name}"')
    
# NOTE: flush_all_block_rules is useful for cleanup but not strictly required 
# for the main app loop, so it is kept as is.
# The original code's list_rules_for_app is redundant for the core logic and is omitted 
# from this fix for brevity.