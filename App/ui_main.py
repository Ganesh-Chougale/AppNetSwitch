from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton,
    QHBoxLayout, QScrollArea, QCheckBox, QSizePolicy
)
from PyQt6.QtCore import Qt, QRect, QSize, QPropertyAnimation, QEasingCurve, pyqtProperty, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen

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
        MainWindow.resize(600, 400)
        self.central_widget = QWidget(MainWindow)
        MainWindow.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
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
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
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
        # Clear previous list
        while self.scroll_layout.count():
            child = self.scroll_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        if not apps:
            self.scroll_layout.addWidget(QLabel("No active user apps found."))
            self.scroll_layout.addStretch()
            return
        for app in apps:
            row = QHBoxLayout()
            row.setSpacing(12)
            icon_label = QLabel("")
            icon_label.setFixedSize(24, 24)
            name_label = QLabel(app["name"])
            name_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            toggle = ToggleSwitch()
            toggle.setChecked(app["path"] not in blocked)
            # Store app info in toggle for later retrieval
            toggle.app_path = app["path"]
            toggle.app_name = app["name"]
            toggle.on_toggle_callback = on_toggle
            # Connect userToggled signal (only fires on user clicks)
            toggle.userToggled.connect(partial(self._on_toggle_user_toggled, toggle))
            self.toggles[app["path"]] = toggle
            row.addWidget(icon_label)
            row.addWidget(name_label)
            row.addStretch()
            row.addWidget(toggle)
            self.scroll_layout.addLayout(row)
        self.scroll_layout.addStretch()
        self.status_label.setText(f"Listed {len(apps)} running user apps.")
    
    def _on_toggle_user_toggled(self, toggle, new_state):
        """Callback for user-initiated toggle changes"""
        print(f"[UI] Toggle clicked for {toggle.app_name}: new_state={new_state} (1=allowed, 0=blocked)")
        toggle.on_toggle_callback(toggle.app_path, toggle.app_name, new_state)