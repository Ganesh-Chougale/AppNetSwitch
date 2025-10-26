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