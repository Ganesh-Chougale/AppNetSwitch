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