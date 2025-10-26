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
            "AppNetSwitch is a powerful application firewall manager\n"
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
