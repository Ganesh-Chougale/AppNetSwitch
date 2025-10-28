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
