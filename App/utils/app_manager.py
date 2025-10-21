import psutil
import os
from .naming_helper import get_app_display_name
from .app_filter import is_system_process, is_system_path

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

def get_running_apps(filter_type="all"):
    """
    Scans for currently running applications.
    
    Args:
        filter_type: "all" (default), "user", or "system"
    
    Returns:
        List of dicts with name, path, pid, and is_system flag
    """
    from .app_filter import filter_apps
    
    apps = []
    seen_paths = set()
    
    for proc in psutil.process_iter(['name', 'exe', 'username', 'pid']):
        try:
            proc_info = proc.info
            # Must have an executable path and a username associated
            if not proc_info.get('exe') or not proc_info.get('username'):
                continue
            
            exe = proc_info['exe']
            
            # Skip if we've seen this executable path before
            if exe in seen_paths:
                continue
                
            # Check if this is a system process
            is_system = is_system_process(proc_info) or is_system_path(exe)
            
            display_name = get_app_display_name(exe, proc_info['name'])
            
            apps.append({
                "name": display_name,
                "path": exe,
                "pid": proc_info['pid'],
                "is_system": is_system
            })
            
            seen_paths.add(exe)
            
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    
    # Apply filter
    apps = filter_apps(apps, filter_type)
    
    # Sort apps: user apps first, then system apps, then alphabetically
    apps.sort(key=lambda x: (x["is_system"], x["name"].lower()))
    return apps