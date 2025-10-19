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
from PyQt6.QtWidgets import QApplication, QMessageBox, QMainWindow # CRITICAL FIX: Import QMainWindow
from PyQt6.QtCore import QTimer
from ui_main import Ui_MainWindow
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
        self.ui.exit_btn.clicked.connect(self.close)
        # Initial population
        self.refresh_app_list()
        self.reapply_blocked()
    def refresh_app_list(self):
        try:
            self.app_list = get_running_apps()
            self.app_data_map = {app["path"]: app for app in self.app_list}
            # CRITICAL FIX: Call populate_app_list on the ui instance
            self.ui.populate_app_list(self.app_list, self.blocked, self.toggle_internet)
            self.ui.status_label.setText(f"Listed {len(self.app_list)} running user apps.")
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
if __name__ == "__main__":
    os_name = platform.system().lower()
    # Permission check
    is_admin = False
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
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
```

App\ui_main.py:
```python
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton,
    QHBoxLayout, QScrollArea, QCheckBox, QSizePolicy
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
        self.setStyleSheet(f"QWidget {{ background-color: {self.hover_color}; padding: 5px; }}")
        super().enterEvent(event)
    def leaveEvent(self, event):
        """Handle mouse leave - restore original color"""
        self.setStyleSheet(f"QWidget {{ background-color: {self.normal_color}; padding: 5px; }}")
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
        MainWindow.setWindowTitle("AppNetSwitch")
        MainWindow.resize(700, 500)
        MainWindow.setMinimumSize(600, 400)
        self.central_widget = QWidget(MainWindow)
        MainWindow.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)
        # Header
        header_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("Refresh")
        self.exit_btn = QPushButton("Exit")
        header_layout.addWidget(self.refresh_btn)
        header_layout.addStretch()
        header_layout.addWidget(self.exit_btn)
        self.main_layout.addLayout(header_layout)
        # Scrollable app list
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { border: 1px solid #ccc; }")
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(0)
        self.scroll_area.setWidget(self.scroll_content)
        self.main_layout.addWidget(self.scroll_area)
        # Status label
        self.status_label = QLabel("Welcome to AppNetSwitch!")
        self.main_layout.addWidget(self.status_label)
        # Storage for toggles
        self.toggles = {}
    def populate_app_list(self, apps, blocked, on_toggle):
        from functools import partial
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
        if not apps:
            self.scroll_layout.addWidget(QLabel("No active user apps found."))
            self.scroll_layout.addStretch()
            return
        for index, app in enumerate(apps):
            # Create a custom row widget with hover support
            row_widget = AppRowWidget()
            row = QHBoxLayout(row_widget)
            row.setContentsMargins(8, 8, 8, 8)
            row.setSpacing(10)
            icon_label = QLabel("🖥")
            icon_label.setFixedSize(24, 24)
            name_label = QLabel(app["name"])
            name_label.setMinimumWidth(200)
            name_label.setMaximumWidth(400)
            name_label.setWordWrap(False)
            # Responsive font size
            font = name_label.font()
            font.setPointSize(10)
            name_label.setFont(font)
            toggle = ToggleSwitch()
            toggle.setChecked(app["path"] not in blocked)
            toggle.setFixedSize(50, 25)
            # Store app info in toggle for later retrieval
            toggle.app_path = app["path"]
            toggle.app_name = app["name"]
            toggle.on_toggle_callback = on_toggle
            # Connect userToggled signal (only fires on user clicks)
            toggle.userToggled.connect(partial(self._on_toggle_user_toggled, toggle))
            self.toggles[app["path"]] = toggle
            # Add widgets to row: icon, name, stretch, toggle
            row.addWidget(icon_label)
            row.addWidget(name_label)
            row.addStretch()
            row.addWidget(toggle)
            # Apply alternating row colors (Option 3)
            # Even rows: white, Odd rows: light gray
            if index % 2 == 0:
                row_widget.setStyleSheet("QWidget { background-color: #FFFFFF; padding: 5px; }")
                row_widget.normal_color = "#FFFFFF"
                row_widget.hover_color = "#E8E8E8"
            else:
                row_widget.setStyleSheet("QWidget { background-color: #F5F5F5; padding: 5px; }")
                row_widget.normal_color = "#F5F5F5"
                row_widget.hover_color = "#EBEBEB"
            # Store reference to UI instance for hover callbacks
            row_widget.ui_instance = self
            # Add row to scroll layout
            self.scroll_layout.addWidget(row_widget)
        # Add final stretch to push everything to the top
        self.scroll_layout.addStretch()
        self.status_label.setText(f"Listed {len(apps)} running user apps.")
    def _on_row_enter(self, row_widget):
        """Handle mouse enter event for row highlighting"""
        # Highlight on hover - darker shade
        if row_widget.is_even:
            row_widget.setStyleSheet("QWidget { background-color: #E8E8E8; }")
        else:
            row_widget.setStyleSheet("QWidget { background-color: #EBEBEB; }")
    def _on_row_leave(self, row_widget):
        """Handle mouse leave event - restore original color"""
        # Restore original alternating color
        row_widget.setStyleSheet(row_widget.original_stylesheet)
    def _on_toggle_user_toggled(self, toggle, new_state):
        """Callback for user-initiated toggle changes"""
        print(f"[UI] Toggle clicked for {toggle.app_name}: new_state={new_state} (1=allowed, 0=blocked)")
        toggle.on_toggle_callback(toggle.app_path, toggle.app_name, new_state)
```

App\utils\app_manager.py:
```python
import psutil
import os
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
            apps.append({
                "name": proc_info['name'],
                "path": exe,
                "pid": proc_info['pid'] # Required for Linux blocking
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return apps
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

App\utils\__init__.py:
```python

```

