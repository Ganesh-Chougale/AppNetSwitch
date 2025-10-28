App\.venv\Scripts\activate.bat:
```batch
@echo off
rem This file is UTF-8 encoded, so we need to update the current code page while executing it
for /f "tokens=2 delims=:." %%a in ('"%SystemRoot%\System32\chcp.com"') do (
    set _OLD_CODEPAGE=%%a
)
if defined _OLD_CODEPAGE (
    "%SystemRoot%\System32\chcp.com" 65001 > nul
)
set "VIRTUAL_ENV=C:\Users\RaSkull\Desktop\Code\AppNetSwitch\App\.venv"
if not defined PROMPT set PROMPT=$P$G
if defined _OLD_VIRTUAL_PROMPT set PROMPT=%_OLD_VIRTUAL_PROMPT%
if defined _OLD_VIRTUAL_PYTHONHOME set PYTHONHOME=%_OLD_VIRTUAL_PYTHONHOME%
set "_OLD_VIRTUAL_PROMPT=%PROMPT%"
set "PROMPT=(.venv) %PROMPT%"
if defined PYTHONHOME set _OLD_VIRTUAL_PYTHONHOME=%PYTHONHOME%
set PYTHONHOME=
if defined _OLD_VIRTUAL_PATH set PATH=%_OLD_VIRTUAL_PATH%
if not defined _OLD_VIRTUAL_PATH set _OLD_VIRTUAL_PATH=%PATH%
set "PATH=%VIRTUAL_ENV%\Scripts;%PATH%"
set "VIRTUAL_ENV_PROMPT=.venv"
:END
if defined _OLD_CODEPAGE (
    "%SystemRoot%\System32\chcp.com" %_OLD_CODEPAGE% > nul
    set _OLD_CODEPAGE=
)
```

App\.venv\Scripts\deactivate.bat:
```batch
@echo off
if defined _OLD_VIRTUAL_PROMPT (
    set "PROMPT=%_OLD_VIRTUAL_PROMPT%"
)
set _OLD_VIRTUAL_PROMPT=
if defined _OLD_VIRTUAL_PYTHONHOME (
    set "PYTHONHOME=%_OLD_VIRTUAL_PYTHONHOME%"
    set _OLD_VIRTUAL_PYTHONHOME=
)
if defined _OLD_VIRTUAL_PATH (
    set "PATH=%_OLD_VIRTUAL_PATH%"
)
set _OLD_VIRTUAL_PATH=
set VIRTUAL_ENV=
set VIRTUAL_ENV_PROMPT=
:END
```

App\data\settings.json:
```json
{
  "blocked": []
}
```

App\firewall\linux.py:
```python
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
```

App\firewall\windows.py:
```python
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
```

App\firewall\__init__.py:
```python
import platform
# Detect OS
OS_NAME = platform.system().lower()
# Dynamic import based on OS
if "windows" in OS_NAME:
    from .windows import block_app, unblock_app
elif "linux" in OS_NAME:
    from .linux import block_app, unblock_app
else:
    raise NotImplementedError(f"Unsupported OS: {OS_NAME}")
```

App\main.py:
```python
import sys
import os
import platform
import traceback
from threading import Thread
from functools import partial
from PyQt6.QtWidgets import QApplication, QMessageBox, QMainWindow
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QIcon
from utils.ui_main import Ui_MainWindow
from utils.about_us import AboutDialog
from firewall import block_app, unblock_app
from utils.app_manager import get_running_apps
from utils.settings_manager import load_settings, save_settings
# CRITICAL FIX: MainWindow must inherit from QMainWindow
class MainWindow(QMainWindow): 
    def __init__(self):
        super().__init__()
        # CRITICAL FIX: Instantiate the UI class and call setupUi on self (the QMainWindow instance)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        # Now, access UI elements via self.ui.refresh_btn
        # Initialize app state
        self.settings = load_settings()
        self.blocked = set(self.settings.get("blocked", []))  # store app_paths
        self.app_data_map = {}  # path → {pid, name}
        # Connect buttons (using self.ui prefix)
        self.ui.refresh_btn.clicked.connect(self.refresh)
        self.ui.about_btn.clicked.connect(self.show_about)
        self.ui.exit_btn.clicked.connect(self.close)
        # Initial population
        self.refresh_app_list()
        self.reapply_blocked()
    def show_about(self):
        """Show the About Us dialog"""
        about_dialog = AboutDialog(
            self,
            portfolio_url="https://ganesh-chougale.github.io/",
            github_url="https://github.com/Ganesh-Chougale",
            linkedin_url="https://www.linkedin.com/in/ganesh-chougale-512449215/"
        )
        about_dialog.exec()
    def refresh_app_list(self):
        try:
            # Get the current filter selection from the UI
            filter_type = self.ui.app_filter.currentText().lower().replace(' apps only', '')
            if filter_type == 'all apps':
                filter_type = 'all'
            # Get apps with the current filter
            self.app_list = get_running_apps(filter_type)
            self.app_data_map = {app["path"]: app for app in self.app_list}
            # Update the UI with the filtered list
            self.ui.populate_app_list(self.app_list, self.blocked, self.toggle_internet)
            # Update status label with filter info
            filter_text = filter_type.capitalize()
            self.ui.status_label.setText(f"Showing {len(self.app_list)} {filter_text} apps")
        except Exception as e:
            print("[ERROR] refresh_app_list:", e)
            traceback.print_exc()
    def reapply_blocked(self):
        print("[INFO] Reapplying previously blocked apps:", self.blocked)
        for app_path in self.blocked:
            app = self.app_data_map.get(app_path)
            if app:
                target = app["pid"] if platform.system().lower() == "linux" else app_path
                Thread(target=self._safe_block, args=(target, app_path, app["name"]), daemon=True).start()
    def toggle_internet(self, app_path, app_name, state):
        app = self.app_data_map.get(app_path)
        if not app:
            print(f"[ERROR] App data not found for path: {app_path}")
            return
        # CRITICAL FIX: Access toggles dictionary via the ui instance
        toggle = self.ui.toggles.get(app_path)
        if toggle:
            toggle.setEnabled(False)
        target = app["pid"] if platform.system().lower() == "linux" else app_path
        # state is True (1) = allowed, False (0) = blocked
        action = "Allow" if state else "Block"
        print(f"[INFO] Toggle: {app_name} → {action}")
        def worker():
            try:
                if state:  # True/checked → Allow (unblock)
                    print(f"[DEBUG] Unblocking {app_name}")
                    unblock_app(target)
                    self.blocked.discard(app_path)
                else:  # False/unchecked → Block
                    print(f"[DEBUG] Blocking {app_name}")
                    block_app(target)
                    self.blocked.add(app_path)
                save_settings({"blocked": list(self.blocked)})
                print(f"[DEBUG] Settings saved. blocked apps: {self.blocked}")
            except Exception as e:
                print(f"[ERROR] toggle_internet for {app_name}: {e}")
                traceback.print_exc()
            finally:
                if toggle:
                    QTimer.singleShot(200, partial(toggle.setEnabled, True))
        Thread(target=worker, daemon=True).start()
    def _safe_block(self, target, app_path, app_name):
        try:
            block_app(target)
        except Exception as e:
            print(f"[ERROR] _safe_block failed for {app_name}: {e}")
            traceback.print_exc()
    def refresh(self):
        try:
            self.blocked = set(load_settings().get("blocked", []))
            self.refresh_app_list()
        except Exception as e:
            print("[ERROR] refresh:", e)
            traceback.print_exc()
def is_admin():
    """Check if the current user has admin privileges"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False
def run_as_admin():
    """Relaunch the script with admin privileges"""
    if platform.system().lower() != 'windows':
        return False
    if is_admin():
        return False  # Already running as admin
    # Re-run the program with admin rights
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, " ".join(sys.argv), None, 1
    )
    return True
if __name__ == "__main__":
    # Add Windows-specific imports
    if platform.system().lower() == 'windows':
        import ctypes
        # Try to elevate if not admin
        if not is_admin():
            print("Requesting administrator privileges...")
            if run_as_admin():
                sys.exit(0)  # Exit the non-elevated instance
    os_name = platform.system().lower()
    is_admin = True  # If we get here, we're either admin or not on Windows
    if os_name == "windows":
        import ctypes
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
    elif os_name == "linux":
        is_admin = (os.geteuid() == 0)
    if not is_admin:
        app = QApplication(sys.argv)
        QMessageBox.critical(
            None,
            "Admin/Root Rights Required",
            "Please run this application as Administrator/Root to modify system firewall rules."
        )
        sys.exit(1)
    app = QApplication(sys.argv)
    # ✅ Universal icon path fix (works for both .py and .exe)
    if getattr(sys, 'frozen', False):
        app_path = sys._MEIPASS
    else:
        app_path = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(app_path, "Extras", "File_Icon.ico")
    app_icon = QIcon(icon_path)
    app.setWindowIcon(app_icon)
    # Create and show main window
    window = MainWindow()
    window.setWindowIcon(app_icon)  # ✅ Ensures top-left & taskbar icon both change
    window.show()
    sys.exit(app.exec())
```

App\utils\about_us.py:
```python
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDesktopServices, QCursor
import webbrowser
class AboutDialog(QDialog):
    def __init__(self, parent=None, portfolio_url="", github_url="", linkedin_url=""):
        super().__init__(parent)
        self.portfolio_url = portfolio_url
        self.github_url = github_url
        self.linkedin_url = linkedin_url
        self.setWindowTitle("About AppNetSwitch")
        self.setModal(True)
        self.setMinimumSize(500, 600)
        self.setMaximumSize(600, 700)
        # Set window style
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
            }
        """)
        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        # App logo
        logo_label = QLabel("AppNetSwitch")
        logo_label.setStyleSheet("""
            QLabel {
                font-size: 36px;
                font-weight: bold;
                color: #2c3e50;
                padding: 20px;
            }
        """)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo_label)
        # App description
        description = QLabel(
            "Application Internet Switch is a powerful app manager\n"
            "that allows you to control network access for your applications."
        )
        description.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #34495e;
                padding: 10px;
            }
        """)
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        description.setWordWrap(True)
        layout.addWidget(description)
        # Version info
        version_label = QLabel("Version 1.0.0")
        version_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #7f8c8d;
                padding: 5px;
            }
        """)
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version_label)
        # Developer info
        developer_label = QLabel("Developed by Ganesh Chougale")
        developer_label.setStyleSheet("""
            QLabel {
                font-size: 13px;
                color: #2c3e50;
                font-weight: bold;
                padding: 5px;
            }
        """)
        developer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(developer_label)
        # Social links section
        links_label = QLabel("Connect with me:")
        links_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #2c3e50;
                padding: 10px 0px 5px 0px;
            }
        """)
        links_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(links_label)
        # Social buttons layout
        social_layout = QHBoxLayout()
        social_layout.setSpacing(15)
        social_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Portfolio button
        if portfolio_url:
            portfolio_btn = self._create_link_button("🌐 Portfolio", portfolio_url, "#3498db")
            social_layout.addWidget(portfolio_btn)
        # GitHub button
        if github_url:
            github_btn = self._create_link_button("💻 GitHub", github_url, "#333333")
            social_layout.addWidget(github_btn)
        # LinkedIn button
        if linkedin_url:
            linkedin_btn = self._create_link_button("💼 LinkedIn", linkedin_url, "#0077b5")
            social_layout.addWidget(linkedin_btn)
        layout.addLayout(social_layout)
        # Spacer
        layout.addStretch()
        # Close button
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 10px 30px;
                font-size: 14px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
        """)
        close_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        self.setLayout(layout)
    def _create_link_button(self, text, url, color):
        """Create a styled button that opens a URL"""
        btn = QPushButton(text)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 13px;
                border-radius: 5px;
                font-weight: bold;
                min-width: 120px;
            }}
            QPushButton:hover {{
                background-color: {self._darken_color(color)};
            }}
            QPushButton:pressed {{
                background-color: {self._darken_color(color, 0.3)};
            }}
        """)
        btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn.clicked.connect(lambda: self._open_url(url))
        return btn
    def _darken_color(self, hex_color, factor=0.2):
        """Darken a hex color by a factor"""
        # Simple darkening - reduce RGB values
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        r = int(r * (1 - factor))
        g = int(g * (1 - factor))
        b = int(b * (1 - factor))
        return f"#{r:02x}{g:02x}{b:02x}"
    def _open_url(self, url):
        """Open URL in default browser"""
        try:
            webbrowser.open(url)
            print(f"[ABOUT] Opening URL: {url}")
        except Exception as e:
            print(f"[ERROR] Failed to open URL: {e}")
```

App\utils\app_filter.py:
```python
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
```

App\utils\app_manager.py:
```python
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
```

App\utils\app_searching.py:
```python
"""
Real-time application searching functionality.
Provides case-insensitive search across app names and paths.
"""
def search_apps(apps: list, search_query: str) -> list:
    """
    Filter apps based on search query (case-insensitive).
    Args:
        apps: List of app dictionaries with 'name' and 'path' keys
        search_query: Search string to filter by
    Returns:
        Filtered list of apps matching the search query
    """
    if not search_query or not search_query.strip():
        return apps
    query = search_query.lower().strip()
    filtered_apps = []
    for app in apps:
        app_name = app.get("name", "").lower()
        app_path = app.get("path", "").lower()
        # Search in both name and path
        if query in app_name or query in app_path:
            filtered_apps.append(app)
    return filtered_apps
def highlight_search_match(text: str, search_query: str) -> str:
    """
    Highlight matching text in search results (for future UI enhancement).
    Args:
        text: Original text
        search_query: Search query to highlight
    Returns:
        Text with HTML highlighting (for QLabel rich text)
    """
    if not search_query or not search_query.strip():
        return text
    # Case-insensitive replacement with highlighting
    import re
    pattern = re.compile(re.escape(search_query), re.IGNORECASE)
    highlighted = pattern.sub(lambda m: f"<b><u>{m.group(0)}</u></b>", text)
    return highlighted
```

App\utils\app_sorting.py:
```python
"""
Application sorting functionality.
Provides various sorting options for the application list.
"""
def sort_apps(apps: list, sort_type: str, blocked_apps: set = None) -> list:
    """
    Sort apps based on the specified sort type.
    Args:
        apps: List of app dictionaries with 'name' and 'path' keys
        sort_type: Type of sorting to apply
        blocked_apps: Set of blocked app paths (for status sorting)
    Returns:
        Sorted list of apps
    """
    if not apps:
        return apps
    blocked_apps = blocked_apps or set()
    # Create a copy to avoid modifying the original list
    sorted_apps = apps.copy()
    if sort_type == "Name (A-Z)":
        sorted_apps.sort(key=lambda app: app.get("name", "").lower())
    elif sort_type == "Name (Z-A)":
        sorted_apps.sort(key=lambda app: app.get("name", "").lower(), reverse=True)
    elif sort_type == "Status (Blocked First)":
        # Blocked apps first, then allowed apps (both sorted by name)
        sorted_apps.sort(key=lambda app: (
            app.get("path", "") not in blocked_apps,  # False (blocked) comes before True (allowed)
            app.get("name", "").lower()
        ))
    elif sort_type == "Status (Allowed First)":
        # Allowed apps first, then blocked apps (both sorted by name)
        sorted_apps.sort(key=lambda app: (
            app.get("path", "") in blocked_apps,  # False (allowed) comes before True (blocked)
            app.get("name", "").lower()
        ))
    return sorted_apps
def get_sort_options() -> list:
    """
    Get available sorting options.
    Returns:
        List of sort option strings
    """
    return [
        "Name (A-Z)",
        "Name (Z-A)",
        "Status (Blocked First)",
        "Status (Allowed First)"
    ]
def get_default_sort() -> str:
    """
    Get the default sort option.
    Returns:
        Default sort option string
    """
    return "Name (A-Z)"
```

App\utils\naming_helper.py:
```python
import platform
import ctypes
import re
from ctypes import wintypes
def parse_executable_name(exe_name: str) -> str:
    """
    Intelligently parse executable name to extract meaningful words.
    Examples:
    - RtkAudioService64.exe -> Realtek Audio Service
    - RAVBg64.exe -> Realtek Audio Console
    - mysqld.exe -> MySQL Server
    - RtkNGUI64.exe -> Realtek Audio Manager
    """
    # Remove .exe extension
    name = exe_name.replace('.exe', '').replace('.dll', '')
    # Known abbreviation mappings
    abbrev_map = {
        'rtk': 'Realtek',
        'rav': 'Realtek Audio',
        'mysql': 'MySQL',
        'svc': 'Service',
        'srv': 'Server',
        'ui': 'UI',
        'ux': 'Experience',
        'bg': 'Background',
        'gui': 'GUI',
        'ngui': 'Audio Manager',
    }
    # Try to split camelCase and snake_case
    # Insert space before uppercase letters (except at start)
    spaced = re.sub(r'([a-z])([A-Z])', r'\1 \2', name)
    # Replace underscores with spaces
    spaced = spaced.replace('_', ' ')
    # Remove numbers and special characters at the end
    spaced = re.sub(r'\d+$', '', spaced).strip()
    # Split into words
    words = spaced.split()
    # Process each word
    processed_words = []
    for word in words:
        word_lower = word.lower()
        # Check if word matches abbreviation
        matched = False
        for abbrev, full_form in abbrev_map.items():
            if word_lower == abbrev or word_lower.startswith(abbrev):
                processed_words.append(full_form)
                matched = True
                break
        # If no abbreviation match and word is meaningful (not just numbers/symbols)
        if not matched and word and not word.isdigit():
            # Capitalize first letter
            processed_words.append(word.capitalize())
    # Join and clean up
    result = ' '.join(processed_words)
    # Remove duplicates while preserving order
    seen = set()
    final_words = []
    for word in result.split():
        word_lower = word.lower()
        if word_lower not in seen:
            final_words.append(word)
            seen.add(word_lower)
    result = ' '.join(final_words)
    # Return original if parsing didn't help
    return result if result and len(result) > 2 else exe_name
def get_app_display_name(exe_path: str, fallback_name: str) -> str:
    """
    Extracts the product name from Windows executable metadata using Windows API.
    Falls back to intelligent parsing of the executable name if metadata is unavailable.
    """
    if platform.system().lower() != "windows":
        return fallback_name
    try:
        # Windows API functions
        GetFileVersionInfoSize = ctypes.windll.version.GetFileVersionInfoSizeW
        GetFileVersionInfo = ctypes.windll.version.GetFileVersionInfoW
        VerQueryValue = ctypes.windll.version.VerQueryValueW
        # Get version info size
        size = GetFileVersionInfoSize(exe_path, None)
        if size == 0:
            # No version info, try intelligent parsing
            return parse_executable_name(fallback_name)
        # Get version info
        version_info = ctypes.create_string_buffer(size)
        GetFileVersionInfo(exe_path, None, size, version_info)
        # Query for ProductName
        product_name_ptr = ctypes.c_wchar_p()
        product_name_len = wintypes.UINT()
        if VerQueryValue(version_info, r'\StringFileInfo\040904B0\ProductName', 
                        ctypes.byref(product_name_ptr), ctypes.byref(product_name_len)):
            product_name = product_name_ptr.value
            if product_name and product_name.strip() and product_name.lower() != 'unknown':
                return product_name.strip()
        # Query for FileDescription
        file_desc_ptr = ctypes.c_wchar_p()
        file_desc_len = wintypes.UINT()
        if VerQueryValue(version_info, r'\StringFileInfo\040904B0\FileDescription', 
                        ctypes.byref(file_desc_ptr), ctypes.byref(file_desc_len)):
            file_desc = file_desc_ptr.value
            if file_desc and file_desc.strip() and file_desc.lower() != 'unknown':
                return file_desc.strip()
    except Exception:
        pass
    # Fallback to intelligent parsing
    return parse_executable_name(fallback_name)
```

App\utils\settings_manager.py:
```python
import json, os
SETTINGS_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "settings.json")
SETTINGS_PATH = os.path.abspath(SETTINGS_PATH)
def load_settings():
    """Load or create default settings.json"""
    if not os.path.exists(os.path.dirname(SETTINGS_PATH)):
        os.makedirs(os.path.dirname(SETTINGS_PATH))
    if not os.path.exists(SETTINGS_PATH):
        save_settings({"blocked": []})
    with open(SETTINGS_PATH, "r") as f:
        return json.load(f)
def save_settings(data: dict):
    with open(SETTINGS_PATH, "w") as f:
        json.dump(data, f, indent=2)
```

App\utils\splash_screen.py:
```python
"""
Splash Screen for AppNetSwitch
Displays a loading screen with SVG logo when the application starts
"""
from PyQt6.QtWidgets import QSplashScreen, QLabel, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QPixmap, QPainter, QColor
from PyQt6.QtSvgWidgets import QSvgWidget
import os
import sys
class SplashScreen(QSplashScreen):
    """Custom splash screen with SVG logo and loading animation"""
    def __init__(self, svg_path, width=400, height=400):
        # Create a transparent pixmap for the splash screen
        pixmap = QPixmap(width, height)
        pixmap.fill(Qt.GlobalColor.transparent)
        super().__init__(pixmap, Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.SplashScreen
        )
        # Set background color
        self.setStyleSheet("""
            QSplashScreen {
                background-color: #ffffff;
                border-radius: 10px;
            }
        """)
        # Create layout
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Add SVG widget
        if os.path.exists(svg_path):
            print(f"[SPLASH] Loading SVG from: {svg_path}")
            self.svg_widget = QSvgWidget(svg_path)
            # Make SVG responsive - it will scale to fit
            self.svg_widget.setMinimumSize(QSize(200, 200))
            self.svg_widget.setMaximumSize(QSize(320, 320))
            layout.addWidget(self.svg_widget, alignment=Qt.AlignmentFlag.AlignCenter)
        else:
            # Fallback if SVG not found
            print(f"[SPLASH] SVG not found at: {svg_path}")
            fallback_label = QLabel("AppNetSwitch")
            fallback_label.setStyleSheet("""
                QLabel {
                    font-size: 32px;
                    font-weight: bold;
                    color: #2c3e50;
                }
            """)
            fallback_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(fallback_label)
        # Add loading text
        self.loading_label = QLabel("Loading...")
        self.loading_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #7f8c8d;
                padding: 10px;
            }
        """)
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.loading_label)
        # Create a container widget and set layout
        container = QWidget()
        container.setLayout(layout)
        container.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                border-radius: 10px;
            }
        """)
        # We can't directly set layout on QSplashScreen, so we'll use a workaround
        # by setting the container as a child widget
        container.setParent(self)
        container.setGeometry(0, 0, width, height)
        # Animation for loading dots
        self.dot_count = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_loading_text)
        self.timer.start(500)  # Update every 500ms
    def update_loading_text(self):
        """Animate the loading text with dots"""
        self.dot_count = (self.dot_count + 1) % 4
        dots = "." * self.dot_count
        self.loading_label.setText(f"Loading{dots}")
    def finish_splash(self, main_window):
        """Close the splash screen and show main window"""
        self.timer.stop()
        self.finish(main_window)
    def drawContents(self, painter):
        """Custom drawing for rounded corners"""
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        super().drawContents(painter)
def get_splash_svg_path():
    """Get the correct path to the splash SVG based on execution mode"""
    if getattr(sys, 'frozen', False):
        # If the application is frozen (compiled with PyInstaller)
        application_path = sys._MEIPASS
        svg_path = os.path.join(application_path, 'Extras', 'loading.svg')
    else:
        # If running from source - get the App directory path
        # This file is in App/utils/, so go up one level to App/
        app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        svg_path = os.path.join(app_dir, 'Extras', 'loading.svg')
    return svg_path
```

App\utils\ui_main.py:
```python
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton,
    QHBoxLayout, QScrollArea, QCheckBox, QSizePolicy, QComboBox, QLineEdit
)
from PyQt6.QtCore import Qt, QRect, QSize, QPropertyAnimation, QEasingCurve, pyqtProperty, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen
# === Custom Row Widget with Hover Support ===
class AppRowWidget(QWidget):
    """Custom widget for app rows with hover highlighting"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.normal_color = "#FFFFFF"
        self.hover_color = "#E8E8E8"
        self.ui_instance = None
    def enterEvent(self, event):
        """Handle mouse enter - highlight on hover"""
        self.setStyleSheet(f"QWidget {{ background-color: {self.hover_color}; }}")
        super().enterEvent(event)
    def leaveEvent(self, event):
        """Handle mouse leave - restore original color"""
        self.setStyleSheet(f"QWidget {{ background-color: {self.normal_color}; }}")
        super().leaveEvent(event)
# === Animated Toggle Switch (CRITICAL FIX APPLIED) ===
class ToggleSwitch(QCheckBox):
    # Custom signal for user-initiated toggles
    userToggled = pyqtSignal(bool)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(50, 25)
        # Use 3 (off position) or (width - height + 3) (on position)
        self._knob_off_pos = 3
        self._knob_on_pos = self.width() - self.height() + 3
        # Initialize knob position based on initial state (which is True/Checked in main.py)
        # This prevents the visual position from being mismatched with the state at startup
        self._knob_pos = self._knob_on_pos if self.isChecked() else self._knob_off_pos
        self.anim = QPropertyAnimation(self, b"knob_pos")
        self.anim.setDuration(200)
        self.anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        # Track if this is user-initiated or programmatic change
        self._user_initiated = False
        # Connect to the state change for animation
        self.stateChanged.connect(self.start_animation)
    @pyqtProperty(int)
    def knob_pos(self):
        return self._knob_pos
    @knob_pos.setter
    def knob_pos(self, value):
        self._knob_pos = value
        self.update()
    def start_animation(self, state):
        # We start the animation from the *current* visual position, 
        # but the end position is determined by the *new* logical state (checked or unchecked)
        self.anim.setStartValue(self._knob_pos)
        # state is 2 for checked, 0 for unchecked
        if self.isChecked(): # Check the new state
            self.anim.setEndValue(self._knob_on_pos)
        else:
            self.anim.setEndValue(self._knob_off_pos)
        # Ensure calculated positions are updated if size changes (e.g. window resize)
        # This is defensively calculating the target positions again
        self._knob_on_pos = self.width() - self.height() + 3
        self._knob_off_pos = 3
        self.anim.start()
    def mousePressEvent(self, event):
        """Override to detect user clicks and toggle state"""
        print(f"[DEBUG] ToggleSwitch mousePressEvent detected")
        new_state = not self.isChecked()
        self._user_initiated = True
        self.setChecked(new_state)
        self._user_initiated = False
        # Emit custom signal
        self.userToggled.emit(new_state)
        print(f"[DEBUG] userToggled signal emitted with state={new_state}")
    def resizeEvent(self, event):
        # Recalculate fixed positions on resize
        self._knob_on_pos = self.width() - self.height() + 3
        self._knob_off_pos = 3
        super().resizeEvent(event)
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRect(0, 0, self.width(), self.height())
        # Draw background based on current CHECKED state (green/red)
        bg_color = QColor("#4CAF50") if self.isChecked() else QColor("#E53935")
        painter.setBrush(QBrush(bg_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(rect, 12, 12)
        # Draw knob at the current animated position
        knob_size = self.height() - 6
        knob_rect = QRect(self._knob_pos, 3, knob_size, knob_size)
        painter.setBrush(QBrush(Qt.GlobalColor.white))
        painter.setPen(QPen(Qt.GlobalColor.black, 0))
        painter.drawEllipse(knob_rect)
# === Main UI Class (Ui_MainWindow and populate_app_list remain as per the last successful fix) ===
# ... (rest of App/ui_main.py remains the same)
class Ui_MainWindow:
    def setupUi(self, MainWindow):
        self.main_window = MainWindow  # Store reference to main window
        MainWindow.setObjectName("MainWindow")
        MainWindow.setWindowTitle("AppNetSwitch")
        MainWindow.resize(800, 600)
        MainWindow.setMinimumSize(600, 400)
        self.central_widget = QWidget(MainWindow)
        MainWindow.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)
        # Header
        header_layout = QHBoxLayout()
        # Left side: Refresh button
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.setToolTip("Refresh the list of running applications")
        # Center: App filter dropdown
        filter_layout = QHBoxLayout()
        filter_label = QLabel("Show:")
        self.app_filter = QComboBox()
        self.app_filter.addItems(["All Apps", "User Apps Only", "System Apps Only"])
        self.app_filter.setCurrentIndex(0)  # Default to "All Apps"
        self.app_filter.setFixedWidth(150)
        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.app_filter)
        # Right side: About and Exit buttons
        self.about_btn = QPushButton("ℹ️ About")
        self.exit_btn = QPushButton("❌ Exit")
        # Add widgets to header
        header_layout.addWidget(self.refresh_btn)
        header_layout.addStretch()
        header_layout.addLayout(filter_layout)
        header_layout.addStretch()
        header_layout.addWidget(self.about_btn)
        header_layout.addWidget(self.exit_btn)
        # Set default filter to 'User Apps Only' (index 1)
        self.app_filter.setCurrentIndex(1)
        # Connect filter change signal
        self.app_filter.currentTextChanged.connect(self.on_filter_changed)
        self.main_layout.addLayout(header_layout)
        # Search and Sort bar
        search_sort_layout = QHBoxLayout()
        # Search box
        search_label = QLabel("🔍 Search:")
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Type to search apps...")
        self.search_box.setClearButtonEnabled(True)
        self.search_box.setMinimumWidth(200)
        self.search_box.setMaximumWidth(400)
        self.search_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.search_box.textChanged.connect(self.on_search_changed)
        # Sort dropdown
        from utils.app_sorting import get_sort_options, get_default_sort
        sort_label = QLabel("Sort by:")
        self.sort_dropdown = QComboBox()
        self.sort_dropdown.addItems(get_sort_options())
        self.sort_dropdown.setCurrentText(get_default_sort())
        self.sort_dropdown.setMinimumWidth(180)
        self.sort_dropdown.setMaximumWidth(220)
        self.sort_dropdown.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.sort_dropdown.currentTextChanged.connect(self.on_sort_changed)
        # Add to layout
        search_sort_layout.addWidget(search_label)
        search_sort_layout.addWidget(self.search_box, 1)  # Allow search box to expand
        search_sort_layout.addSpacing(20)
        search_sort_layout.addWidget(sort_label)
        search_sort_layout.addWidget(self.sort_dropdown, 0)  # Fixed size
        search_sort_layout.addStretch()
        self.main_layout.addLayout(search_sort_layout)
        # Scrollable app list
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { border: 1px solid #ccc; }")
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(0)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)  # Align items to top
        self.scroll_area.setWidget(self.scroll_content)
        self.main_layout.addWidget(self.scroll_area)
        # Status label
        self.status_label = QLabel("Welcome to AppNetSwitch!")
        self.main_layout.addWidget(self.status_label)
        # Storage for toggles and app data
        self.toggles = {}
        self.all_apps = []  # Store all apps for filtering
        self.blocked_apps = set()  # Store blocked apps
        self.on_toggle_callback = None  # Store toggle callback
    def populate_app_list(self, apps, blocked, on_toggle):
        from functools import partial
        from utils.app_filter import categorize_apps
        from utils.app_searching import search_apps
        from utils.app_sorting import sort_apps
        # Store data for search and sort operations
        self.all_apps = apps
        self.blocked_apps = blocked
        self.on_toggle_callback = on_toggle
        # Apply search filter (case-insensitive, real-time)
        search_query = self.search_box.text()
        filtered_apps = search_apps(apps, search_query)
        # Apply sorting
        sort_type = self.sort_dropdown.currentText()
        sorted_apps = sort_apps(filtered_apps, sort_type, blocked)
        self.toggles.clear()
        # Clear previous list completely
        while self.scroll_layout.count() > 0:
            item = self.scroll_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                # Recursively delete layouts
                while item.layout().count():
                    child = item.layout().takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()
        if not sorted_apps:
            no_results = QLabel("No applications found matching the current filter.")
            no_results.setStyleSheet("color: #7f8c8d; padding: 20px; font-size: 12px;")
            self.scroll_layout.addWidget(no_results)
            self.scroll_layout.addStretch()
            return
        # Categorize apps
        user_apps, system_apps = categorize_apps(sorted_apps)
        # Add user apps section
        if user_apps:
            user_header = QLabel("<b>User Applications</b>")
            user_header.setStyleSheet("color: #2c3e50; padding: 8px 10px; background-color: #ecf0f1;")
            user_header.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            user_header.setMinimumHeight(30)
            user_header.setMaximumHeight(30)
            self.scroll_layout.addWidget(user_header)
            for app in user_apps:
                self._add_app_row(app, blocked, on_toggle, is_system=False)
        # Add system apps section if there are any
        if system_apps:
            system_header = QLabel("<b>System Applications</b>")
            system_header.setStyleSheet("color: #7f8c8d; padding: 8px 10px; background-color: #f8f9fa;")
            system_header.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            system_header.setMinimumHeight(30)
            system_header.setMaximumHeight(30)
            self.scroll_layout.addWidget(system_header)
            for app in system_apps:
                self._add_app_row(app, blocked, on_toggle, is_system=True)
        # Add stretch at the end to push all items to the top
        self.scroll_layout.addStretch()
    def _add_app_row(self, app, blocked, on_toggle, is_system=False):
        from functools import partial
        # Create a custom row widget with hover support
        row_widget = AppRowWidget()
        row_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        row_widget.setMinimumHeight(40)  # Consistent row height
        row_widget.setMaximumHeight(40)  # Prevent expansion
        row = QHBoxLayout(row_widget)
        row.setContentsMargins(8, 8, 8, 8)
        row.setSpacing(10)
        # Apply alternating row colors
        row_count = self.scroll_layout.count()
        if row_count % 2 == 0:
            row_widget.setStyleSheet("QWidget { background-color: #FFFFFF; }")
            row_widget.normal_color = "#FFFFFF"
            row_widget.hover_color = "#E8E8E8"
        else:
            row_widget.setStyleSheet("QWidget { background-color: #F5F5F5; }")
            row_widget.normal_color = "#F5F5F5"
            row_widget.hover_color = "#EBEBEB"
        # App icon (using emoji for now)
        icon = "🛠️" if is_system else "🖥️"
        icon_label = QLabel(icon)
        icon_label.setFixedSize(24, 24)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # App name with tooltip showing full path
        name_label = QLabel(app["name"])
        name_label.setToolTip(f"{app['name']}\n{app['path']}")
        # Make it responsive - no fixed widths
        name_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        name_label.setMinimumHeight(25)  # Fixed height to prevent expansion
        name_label.setMaximumHeight(25)  # Fixed height to prevent expansion
        # Use elision for long text instead of wrapping
        name_label.setTextFormat(Qt.TextFormat.PlainText)
        name_label.setWordWrap(False)
        # Enable text elision (add ... for long text)
        font_metrics = name_label.fontMetrics()
        elided_text = font_metrics.elidedText(app["name"], Qt.TextElideMode.ElideRight, 9999)
        name_label.setText(elided_text)
        # Style system apps differently
        if is_system:
            name_label.setStyleSheet("color: #7f8c8d;")
        # Responsive font size
        font = name_label.font()
        font.setPointSize(10)
        name_label.setFont(font)
        # Toggle switch
        toggle = ToggleSwitch()
        toggle.setChecked(app["path"] not in blocked)
        toggle.setFixedSize(50, 25)
        toggle.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        # Add widgets to row - no stretch between name and toggle
        row.addWidget(icon_label, 0)  # Fixed size
        row.addWidget(name_label, 1)  # Expand to fill available space
        row.addWidget(toggle, 0)  # Fixed size
        # Store app info in toggle for later retrieval
        toggle.app_path = app["path"]
        toggle.app_name = app["name"]
        # Connect toggle signal with proper parameter handling
        toggle.userToggled.connect(lambda checked, path=app["path"], name=app["name"]: on_toggle(path, name, checked))
        # Store reference to toggle
        self.toggles[app["path"]] = toggle
        # Store reference to UI instance for hover callbacks
        row_widget.ui_instance = self
        # Add row to layout
        self.scroll_layout.addWidget(row_widget)
    def _on_row_enter(self, row_widget):
        """Handle mouse enter event for row highlighting"""
        # Highlight on hover - darker shade
        if row_widget.is_even:
            row_widget.setStyleSheet("QWidget { background-color: #E8E8E8; }")
        else:
            row_widget.setStyleSheet("QWidget { background-color: #EBEBEB; }")
    def _on_row_leave(self, row_widget):
        """Handle mouse leave event for row highlighting"""
        # Restore normal background
        if row_widget.is_even:
            row_widget.setStyleSheet("QWidget { background-color: #FFFFFF; }")
        else:
            row_widget.setStyleSheet("QWidget { background-color: #F5F5F5; }")
    def on_filter_changed(self, filter_text):
        """Handle filter dropdown changes"""
        # Call refresh directly on the main window
        if hasattr(self.main_window, 'refresh'):
            self.main_window.refresh()
    def on_search_changed(self, search_text):
        """Handle real-time search input changes"""
        # Re-populate the list with current search query
        if hasattr(self, 'all_apps') and self.all_apps:
            self.populate_app_list(self.all_apps, self.blocked_apps, self.on_toggle_callback)
            # Update status label
            from utils.app_searching import search_apps
            filtered_count = len(search_apps(self.all_apps, search_text))
            if search_text.strip():
                self.main_window.ui.status_label.setText(
                    f"Found {filtered_count} app(s) matching '{search_text}'"
                )
            else:
                self.main_window.ui.status_label.setText(
                    f"Showing {len(self.all_apps)} apps"
                )
    def on_sort_changed(self, sort_text):
        """Handle sort dropdown changes"""
        # Re-populate the list with current sort option
        if hasattr(self, 'all_apps') and self.all_apps:
            self.populate_app_list(self.all_apps, self.blocked_apps, self.on_toggle_callback)
    def _on_toggle_user_toggled(self, toggle, new_state):
        """Callback for user-initiated toggle changes"""
        print(f"[UI] Toggle clicked for {toggle.app_name}: new_state={new_state} (1=allowed, 0=blocked)")
        toggle.on_toggle_callback(toggle.app_path, toggle.app_name, new_state)
```

App\utils\__init__.py:
```python

```


---

After finishing all code summary of App
Codex\Features\Scripts\CodeSummary.js:
```js
const fs = require("fs");
const path = require("path");
// ⚙️ Config object for switches
const config = {
  reduceTokensByWhiteSpace: false,
  checkOldOutput: false,    // 🔥 Compare with old summary
  skipLanguages: ["text", ".md"], // can be ".css" or "css" or mixed
  removeComments: false     // ✅ true = strip comments, false = keep them
};
// Supported file extensions and languages
const supportedExtensions = {
  ".js": "js",
  ".gs": "gs",
  ".html": "html",
  ".ts": "typescript",
  ".java": "java",
  ".py": "python",
  ".go": "go",
  ".rb": "ruby",
  ".cpp": "cpp",
  ".c": "c",
  ".php": "php",
  ".sh": "bash",
  ".cs": "csharp",
  ".css": "css",
  ".txt": "text",
  ".h": "cpp",
  ".yaml": "yaml",
  ".dart": "dart",
  ".tsx": "typescript",
  ".mjs": "javascript",
  ".env": "env",
  ".reg": "registry",
  ".bat": "batch",
  ".cmd": "batch",
  ".md": "markdown",
  ".json": "json",       // ✅ Added JSON support
  ".xml": "xml"          // ✅ Added XML support
};
// 🔑 Normalize skipLanguages so it can take both extensions (.css) or language names (css)
const normalizedSkipLanguages = config.skipLanguages.map((item) =>
  item.startsWith(".") ? supportedExtensions[item] || item.replace(".", "") : item
);
// Ignored files and folders
const ignoredFiles = [
  "site", ".metadata", "libraries", "gradle", ".angular", ".vscode", "node_modules", ".editorconfig",
  ".gitignore", "Migrations", "Debug", "test", "libs", "angular.json", "package-lock.json",
  "package.json", "README.md", "Dependencies", "Connected Services", "tsconfig.app.json", "next-env.d.ts",
  "tsconfig.json", "tsconfig.spec.json", "CodeSummary.md", ".mvn", ".settings", "build", "next.config.ts",
  "cS.js", "CS.js", ".idea", ".next", "ErrorExporter.js", "Splitter.js", ".dart_tool", "io", "plugins", "flutter"
  , "CodeSummer.js", "FileAndFolderSummary.js"
];
let processedFiles = 0;
let totalFiles = 0;
let lastDir = "";
// Walk a directory
function walkDir(dir, callback) {
  if (!fs.existsSync(dir)) return;
  for (const file of fs.readdirSync(dir)) {
    const filePath = path.join(dir, file);
    const stats = fs.statSync(filePath);
    stats.isDirectory() ? walkDir(filePath, callback) : callback(filePath);
  }
}
// ⚙️ Strip comments from code
function stripComments(content, lang) {
  switch (lang) {
    case "js": case "ts": case "java": case "c": case "cpp": case "csharp": case "php":
      return content.replace(/\/\/.*$/gm, "").replace(/\/\*[\s\S]*?\*\//gm, "");
    case "python": case "ruby": case "bash": case "shell": case "dockerfile":
      return content.replace(/#.*$/gm, "");
    case "html": case "xml": case "vue": case "svelte":      // ✅ XML support here
      return content.replace(/<!--[\s\S]*?-->/gm, "");
    case "css": case "scss": case "less":
      return content.replace(/\/\*[\s\S]*?\*\//gm, "");
    case "yaml": case "yml": case "ini": case "toml":
      return content.replace(/^\s*#.*/gm, "");
    case "sql":
      return content.replace(/--.*$/gm, "").replace(/\/\*[\s\S]*?\*\//gm, "");
    case "json":                                       // ✅ JSON support here
      return content;
    default:
      return content;
  }
}
// ✅ Clean empty lines + optional whitespace formatting
function removeExcessiveEmptyLines(content) {
  return content
    .replace(/\r\n/g, "\n")
    .split("\n")
    .filter((line) => line.trim() !== "")
    .map((line) => (config.reduceTokensByWhiteSpace ? line.trimStart() : line))
    .join("\n")
    .trim();
}
// 🔎 Parse CodeSummary.md into { filePath: snippet }
function parseSummary(summaryText) {
  const snippetRegex = /([^\n]+):\n```(\w+)\n([\s\S]*?)```/g;
  const snippets = {};
  let match;
  while ((match = snippetRegex.exec(summaryText))) {
    snippets[match[1].trim()] = match[3].trim();
  }
  return snippets;
}
// 📝 Generate summary
function generateSummary(root, selectedDirs) {
  let summary = "";
  processedFiles = 0;
  totalFiles = 0;
  lastDir = "";
  console.log("🔍 Starting scan...");
  const targets =
    selectedDirs.length > 0
      ? selectedDirs.map((folder) => path.resolve(folder)).filter(fs.existsSync)
      : [root];
  // Count total files
  targets.forEach((dir) => {
    walkDir(dir, (filePath) => {
      const ext = path.extname(filePath).toLowerCase();
      const lang = supportedExtensions[ext];
      const relativeFilePath = path.relative(root, filePath);
      if (
        !lang ||
        ignoredFiles.some((ignored) => relativeFilePath.includes(ignored)) ||
        normalizedSkipLanguages.includes(lang)
      ) return;
      totalFiles++;
    });
  });
  console.log(`📄 Total files to process: ${totalFiles}`);
  const newSnippets = {};
  targets.forEach((dir) => {
    walkDir(dir, (filePath) => {
      const ext = path.extname(filePath).toLowerCase();
      const lang = supportedExtensions[ext];
      const relativeFilePath = path.relative(root, filePath);
      if (
        !lang ||
        ignoredFiles.some((ignored) => relativeFilePath.includes(ignored)) ||
        normalizedSkipLanguages.includes(lang)
      ) return;
      let content = fs.readFileSync(filePath, "utf-8");
      const currentDir = path.dirname(relativeFilePath).split(path.sep)[0];
      if (currentDir !== lastDir) {
        if (lastDir) summary += `\n---\n\nAfter finishing all code summary of ${lastDir}\n`;
        lastDir = currentDir;
      }
      console.log(`Processing: ${relativeFilePath}`);
      if (config.removeComments) content = stripComments(content, lang);
      content = removeExcessiveEmptyLines(content);
      newSnippets[relativeFilePath] = content;
      summary += `${relativeFilePath}:\n\`\`\`${lang}\n${content}\n\`\`\`\n\n`;
      processedFiles++;
      const progress = Math.round((processedFiles / totalFiles) * 100);
      process.stdout.write(`\rProgress: ${progress}%`);
    });
  });
  const outputDir = path.join(__dirname, "ScriptOutput");
  fs.mkdirSync(outputDir, { recursive: true });
  const oldPath = path.join(outputDir, "CodeSummary.md");
  if (config.checkOldOutput) {
    let oldSnippets = {};
    if (fs.existsSync(oldPath)) oldSnippets = parseSummary(fs.readFileSync(oldPath, "utf-8"));
    let unchangedSection = "# unchanged snippets\n\n";
    let changedSection = "# changed snippets\n\n";
    const allFiles = new Set([...Object.keys(oldSnippets), ...Object.keys(newSnippets)]);
    allFiles.forEach((file) => {
      const oldCode = oldSnippets[file];
      const newCode = newSnippets[file];
      const ext = path.extname(file).toLowerCase();
      const lang = supportedExtensions[ext] || "";
      if (oldCode && newCode) {
        if (oldCode === newCode) {
          unchangedSection += `${file}:\n\`\`\`${lang}\n${newCode}\n\`\`\`\n\n`;
        } else {
          changedSection += `${file} (snippet changed):\n\`\`\`${lang}\n${newCode}\n\`\`\`\n\n`;
        }
      } else if (!oldCode && newCode) {
        changedSection += `${file} (new file):\n\`\`\`${lang}\n${newCode}\n\`\`\`\n\n`;
      } else if (oldCode && !newCode) {
        changedSection += `${file} (removed file)\n\n`;
      }
    });
    fs.writeFileSync(oldPath, unchangedSection + changedSection);
  } else {
    fs.writeFileSync(oldPath, summary);
  }
  console.log("\n✅ Done! Summary saved to CodeSummary.md");
}
// 🏁 MAIN
const rootDir = process.cwd();
const selectedDirs = process.argv.slice(2);
generateSummary(rootDir, selectedDirs);
```

Codex\Features\Scripts\FixedText.js:
```js
const fs = require("fs");
const path = require("path");
function main() {
  const inputFile = path.join(__dirname, "..", "..", "Input", "Fixed.md");
  const outputDir = path.join(__dirname, "ScriptOutput");
  fs.mkdirSync(outputDir, { recursive: true });
  let content = "";
  if (fs.existsSync(inputFile)) {
    content = fs.readFileSync(inputFile, "utf-8");
  } else {
    content = "_No fixed text provided._";
  }
  fs.writeFileSync(path.join(outputDir, "FixedText.md"), content);
  console.log("✅ FixedText.md generated from Input/Fixed.md");
}
main();
```

Codex\Runner.js:
```js
const fs = require("fs");
const { spawnSync } = require("child_process");
const path = require("path");
// ✅ Switches
const config = {
  runCodeSummary: true,
  runFolderStructurer: true,
  runFixedText: false,
  runTriedSolutions: false,
  runFinalInstruction: false,
};
// small helpers (no external PathMaker)
function scriptPath(...parts) {
  return path.join(__dirname, "Features", "Scripts", ...parts);
}
function scriptOutputPath(...parts) {
  return path.join(__dirname, "Features", "Scripts", "ScriptOutput", ...parts);
}
// ✅ Run feature
function runFeature(scriptPathStr, args = []) {
  console.log(`▶ Running ${scriptPathStr} ${args.length ? args.join(" ") : ""}...`);
  const res = spawnSync("node", [scriptPathStr, ...args], { stdio: "inherit" });
  if (res.error) {
    console.error("⚠️ spawnSync error:", res.error);
  } else if (typeof res.status === "number" && res.status !== 0) {
    console.warn(`⚠️ Script exited with code ${res.status} (${scriptPathStr})`);
  }
}
// ✅ Collect outputs (in requested order)
function collectOutputs() {
  const outputDir = path.join(__dirname, "Output");
  fs.mkdirSync(outputDir, { recursive: true });
  const outputPath = path.join(outputDir, "output.md");
  let finalOutput = "# Codebase Report\n\n";
  // 1️⃣ Folder Structure
  if (config.runFolderStructurer) {
    const file = scriptOutputPath("FileAndFolderSummary.md");
    if (fs.existsSync(file)) {
      finalOutput += "## Folder Structure\n" + fs.readFileSync(file, "utf-8") + "\n\n---\n\n";
    }
  }
  // 2️⃣ Fixed Text
  if (config.runFixedText) {
    const file = scriptOutputPath("FixedText.md");
    if (fs.existsSync(file)) {
      finalOutput += "## Fixed Text\n" + fs.readFileSync(file, "utf-8") + "\n\n---\n\n";
    }
  }
  // 3️⃣ Code Summary
  if (config.runCodeSummary) {
    const file = scriptOutputPath("CodeSummary.md");
    if (fs.existsSync(file)) {
      finalOutput += "## Code Summary\n" + fs.readFileSync(file, "utf-8") + "\n\n---\n\n";
    } else {
      finalOutput += "## Code Summary\n\n_(no code summary found)_\n\n---\n\n";
    }
  }
  // 4️⃣ Tried Solutions (optional)
  if (config.runTriedSolutions) {
    const file = scriptOutputPath("TriedSolutions.md");
    if (fs.existsSync(file)) {
      finalOutput += "## Previous Takes\n" + fs.readFileSync(file, "utf-8") + "\n\n---\n\n";
    }
  }
  fs.writeFileSync(outputPath, finalOutput, "utf-8");
  console.log(`✅ Combined report generated at ${outputPath}`);
  return outputPath;
}
// 🏁 MAIN
function main() {
  const args = process.argv.slice(2);
  const projectPath = args[0] ? args[0] : process.cwd();
  console.log(`📂 Running Codex on: ${projectPath}`);
  // run scripts (they accept projectPath where relevant)
  if (config.runFolderStructurer) runFeature(scriptPath("FileAndFolderSummary.js"), [projectPath]);
  if (config.runCodeSummary) runFeature(scriptPath("CodeSummary.js"), [projectPath]);
  if (config.runFixedText) runFeature(scriptPath("FixedText.js"));
  if (config.runTriedSolutions) runFeature(scriptPath("TriedSolutions.js"));
  const outputPath = collectOutputs();
  // Run final instruction after merging
  if (config.runFinalInstruction) {
    runFeature(scriptPath("FinalInstruction.js"));
    const instrFile = scriptOutputPath("FinalInstruction.md"); // ✅ corrected
    if (fs.existsSync(instrFile)) {
      const extra = fs.readFileSync(instrFile, "utf-8");
      const outputContent = fs.readFileSync(outputPath, "utf-8");
      if (!outputContent.includes(extra)) {
        fs.appendFileSync(outputPath, "\n\n## Final Instruction\n" + extra, "utf-8");
        console.log("✅ Final instruction appended.");
      }
    }
  }
}
main();
```

