#!/usr/bin/env python3
"""Simple test to verify toggle switch works"""

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt

# Import the toggle switch
from ui_main import ToggleSwitch

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Toggle Test")
        self.resize(300, 200)
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Add label
        label = QLabel("Click the toggle below:")
        layout.addWidget(label)
        
        # Add toggle
        self.toggle = ToggleSwitch()
        self.toggle.setChecked(True)
        layout.addWidget(self.toggle)
        
        # Add status label
        self.status = QLabel("Status: Waiting for click...")
        layout.addWidget(self.status)
        
        # Connect state changed
        self.toggle.stateChanged.connect(self.on_state_changed)
        
        layout.addStretch()
    
    def on_state_changed(self):
        state = self.toggle.isChecked()
        user_initiated = self.toggle._user_initiated
        print(f"[TEST] State changed: checked={state}, user_initiated={user_initiated}")
        self.status.setText(f"Status: Checked={state}, User={user_initiated}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    print("[TEST] Window opened. Try clicking the toggle...")
    sys.exit(app.exec())
