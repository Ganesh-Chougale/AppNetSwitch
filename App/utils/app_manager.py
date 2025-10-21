import psutil
import os
from .naming_helper import get_app_display_name

# Updated list of known system paths and processes for better filtering
SYSTEM_PATHS = [
    "c:\\windows\\system32", "c:\\windows\\syswow64", "/usr/bin/", "/usr/sbin/",
    "/lib/", "/sbin/", "/dev/", "/proc/", "/opt/google/chrome" # Common system paths
]

SYSTEM_NAMES = [
    "svchost.exe", "system", "init", "kworker", "systemd", "explorer.exe",
    "winlogon.exe", "csrss.exe", "smss.exe", "lsass.exe", "dbus-daemon",
    "gnome-shell", "kdeinit5", "xfce4-session"
]

def is_system_process(proc_info: dict) -> bool:
    """Checks if a process is a known system or background process."""
    if not proc_info.get('exe'):
        return True
    
    exe_path = proc_info['exe'].lower()
    name = proc_info['name'].lower()
    
    # Filter by common system paths
    if any(exe_path.startswith(path.lower()) for path in SYSTEM_PATHS):
        # Allow common desktop environment components (e.g., shell/terminal)
        if os.path.basename(exe_path) not in ("bash", "zsh", "gnome-terminal", "konsole"):
            return True

    # Filter by common system names
    if name in SYSTEM_NAMES or name.endswith(".dll"):
        return True
        
    return False

def get_running_apps():
    """
    Scans for currently running user applications, filtering system processes.
    Returns a list of dicts with name, path, and pid.
    """
    apps = []
    seen_paths = set()
    
    for proc in psutil.process_iter(['name', 'exe', 'username', 'pid']):
        try:
            proc_info = proc.info
            # Must have an executable path and a username associated
            if not proc_info.get('exe') or not proc_info.get('username'):
                continue
                
            if is_system_process(proc_info):
                continue
                
            exe = proc_info['exe']
            
            # Filter out multiple instances of the same executable path
            if exe in seen_paths:
                continue
                
            seen_paths.add(exe)
            
            display_name = get_app_display_name(exe, proc_info['name'])
            
            apps.append({
                "name": display_name,
                "path": exe,
                "pid": proc_info['pid']
            })
            
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
            
    return apps