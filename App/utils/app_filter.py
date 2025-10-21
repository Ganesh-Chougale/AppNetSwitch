"""
app_filter.py - Provides functionality to filter and categorize running applications.
"""
import os

# Known system paths and processes for filtering
SYSTEM_PATHS = [
    "c:\\windows\\system32", "c:\\windows\\syswow64", "c:\\windows\\winsxs",
    "c:\\program files\\windowsapps", "c:\\program files (x86)\\windowsapps",
    "/usr/bin/", "/usr/sbin/", "/lib/", "/sbin/", "/dev/", "/proc/"
]

SYSTEM_NAMES = [
    "svchost", "system", "init", "kworker", "systemd", "explorer.exe",
    "winlogon.exe", "csrss.exe", "smss.exe", "lsass.exe", "dbus-daemon",
    "gnome-shell", "kdeinit5", "xfce4-session", "services.exe", "lsm.exe",
    "wininit.exe", "taskhostw.exe", "dwm.exe", "fontdrvhost.exe"
]

def is_system_path(path: str) -> bool:
    """Check if a path is in a system directory."""
    if not path or not isinstance(path, str):
        return False
    
    path_lower = path.lower()
    return any(path_lower.startswith(sys_path.lower()) for sys_path in SYSTEM_PATHS)

def is_system_process(proc_info: dict) -> bool:
    """Check if a process is a known system or background process."""
    if not proc_info.get('exe') or not proc_info.get('name'):
        return True
    
    exe_path = proc_info['exe'].lower()
    name = proc_info['name'].lower()
    
    # Check system paths and names
    if (is_system_path(exe_path) or 
        any(system_name in name for system_name in SYSTEM_NAMES) or
        name.endswith(('.dll', '.sys', '.drv'))):
        return True
        
    # Allow common desktop environment components
    if os.path.basename(exe_path) in ("bash", "zsh", "gnome-terminal", "konsole"):
        return False
        
    return False

def filter_apps(apps, filter_type="all"):
    """
    Filter applications based on the specified filter type.
    
    Args:
        apps: List of app dictionaries (must include 'is_system' key)
        filter_type: "all", "user", or "system"
        
    Returns:
        Filtered list of apps
    """
    if filter_type == "user":
        return [app for app in apps if not app.get('is_system', False)]
    elif filter_type == "system":
        return [app for app in apps if app.get('is_system', False)]
    return apps

def categorize_apps(apps):
    """
    Categorize apps into user and system apps.
    
    Returns:
        Tuple of (user_apps, system_apps)
    """
    user_apps = [app for app in apps if not app.get('is_system', False)]
    system_apps = [app for app in apps if app.get('is_system', False)]
    return user_apps, system_apps
