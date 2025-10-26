try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    print("WebEngine is available")
except ImportError as e:
    print(f"WebEngine NOT available: {e}")
