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
        svg_path = os.path.join(application_path, 'ui', 'resources', 'loading.svg')
    else:
        # If running from source - get the ui/resources directory path
        # This file is in app/ui/, so resources is in the same directory
        ui_dir = os.path.dirname(os.path.abspath(__file__))
        svg_path = os.path.join(ui_dir, 'resources', 'loading.svg')
    
    return svg_path
