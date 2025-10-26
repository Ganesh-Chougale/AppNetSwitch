try:
    from PyQt6.QtSvg import QSvgRenderer
    print("SVG support is available")
except ImportError as e:
    print(f"SVG support NOT available: {e}")
