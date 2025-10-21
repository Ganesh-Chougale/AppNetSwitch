from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton,
    QHBoxLayout, QScrollArea, QCheckBox, QSizePolicy, QComboBox
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
        
        # Right side: Exit button
        self.exit_btn = QPushButton("❌ Exit")
        
        # Add widgets to header
        header_layout.addWidget(self.refresh_btn)
        header_layout.addStretch()
        header_layout.addLayout(filter_layout)
        header_layout.addStretch()
        header_layout.addWidget(self.exit_btn)
        
        # Set default filter to 'User Apps Only' (index 1)
        self.app_filter.setCurrentIndex(1)
        
        # Connect filter change signal
        self.app_filter.currentTextChanged.connect(self.on_filter_changed)
        
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
        from utils.app_filter import categorize_apps
        
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
            self.scroll_layout.addWidget(QLabel("No applications found matching the current filter."))
            self.scroll_layout.addStretch()
            return
            
        # Categorize apps
        user_apps, system_apps = categorize_apps(apps)
        
        # Add user apps section
        if user_apps:
            user_header = QLabel("<b>User Applications</b>")
            user_header.setStyleSheet("color: #2c3e50; margin-top: 10px; margin-bottom: 5px;")
            self.scroll_layout.addWidget(user_header)
            
            for app in user_apps:
                self._add_app_row(app, blocked, on_toggle, is_system=False)
        
        # Add system apps section if there are any
        if system_apps:
            system_header = QLabel("<b>System Applications</b>")
            system_header.setStyleSheet("color: #7f8c8d; margin-top: 15px; margin-bottom: 5px;")
            self.scroll_layout.addWidget(system_header)
            
            for app in system_apps:
                self._add_app_row(app, blocked, on_toggle, is_system=True)
    
    def _add_app_row(self, app, blocked, on_toggle, is_system=False):
        from functools import partial
        
        # Create a custom row widget with hover support
        row_widget = AppRowWidget()
        row = QHBoxLayout(row_widget)
        row.setContentsMargins(8, 8, 8, 8)
        row.setSpacing(10)
        
        # Apply alternating row colors
        row_count = self.scroll_layout.count()
        if row_count % 2 == 0:
            row_widget.setStyleSheet("QWidget { background-color: #FFFFFF; padding: 5px; }")
            row_widget.normal_color = "#FFFFFF"
            row_widget.hover_color = "#E8E8E8"
        else:
            row_widget.setStyleSheet("QWidget { background-color: #F5F5F5; padding: 5px; }")
            row_widget.normal_color = "#F5F5F5"
            row_widget.hover_color = "#EBEBEB"
        
        # App icon (using emoji for now)
        icon = "🛠️" if is_system else "🖥️"
        icon_label = QLabel(icon)
        icon_label.setFixedSize(24, 24)
        
        # App name with tooltip showing full path
        name_label = QLabel(app["name"])
        name_label.setToolTip(f"{app['name']}\n{app['path']}")
        name_label.setMinimumWidth(200)
        name_label.setMaximumWidth(400)
        name_label.setWordWrap(False)
        
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
        
        # Add widgets to row
        row.addWidget(icon_label)
        row.addWidget(name_label, 1)  # Allow name to expand
        row.addStretch()
        row.addWidget(toggle)
        
        # Store app info in toggle for later retrieval
        toggle.app_path = app["path"]
        toggle.app_name = app["name"]
        
        # Connect toggle signal
        toggle.userToggled.connect(partial(on_toggle, app_path=app["path"]))
        
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
    
    def _on_toggle_user_toggled(self, toggle, new_state):
        """Callback for user-initiated toggle changes"""
        print(f"[UI] Toggle clicked for {toggle.app_name}: new_state={new_state} (1=allowed, 0=blocked)")
        toggle.on_toggle_callback(toggle.app_path, toggle.app_name, new_state)