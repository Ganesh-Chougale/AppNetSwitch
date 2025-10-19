## 🧩 **Phase 1 — Setup & Foundation**

**Goal:** Get your environment clean and ready.

**Steps:**

1. ✅ Install **Python 3.11+**
2. ✅ Create a project folder → `app_firewall`
3. ✅ Set up virtual environment

   ```bash
   python -m venv .venv
   ```
4. ✅ Activate it (`.venv\Scripts\activate` or `source .venv/bin/activate`)
5. ✅ Install basics

   ```bash
   pip install pyqt6 psutil pyinstaller
   ```
6. ✅ Create folder structure:

   ```
   app_firewall/
     ├── main.py
     ├── ui_main.py
     ├── firewall/
     │   ├── __init__.py
     │   ├── windows.py
     │   └── linux.py
     └── utils/
         └── app_manager.py
   ```

---

## ⚙️ **Phase 2 — UI Design (PyQt6)**

**Goal:** Design a clean desktop interface.

**Steps:**

1. Use **Qt Designer** (comes with PyQt)

   * Add a list or table to show apps
   * Add toggle switches beside each
   * Add buttons: “Refresh” & “Apply Changes”
2. Save UI → `ui_main.ui`
3. Convert to Python:

   ```bash
   pyuic6 ui_main.ui -o ui_main.py
   ```
4. Connect buttons & switches in `main.py`

---

## 🔌 **Phase 3 — OS Integration Layer**

**Goal:** Add backend logic for controlling internet access.

**Steps:**

1. In `firewall/windows.py`:

   * Use `subprocess.run(["netsh", "advfirewall", "firewall", ...])`
   * Create functions:

     ```python
     def block_app(path): ...
     def unblock_app(path): ...
     ```
2. In `firewall/linux.py`:

   * Use `iptables` commands:

     ```python
     sudo iptables -A OUTPUT -m owner --pid-owner <pid> -j DROP
     ```
3. In `main.py`, detect OS with:

   ```python
   import platform
   os_name = platform.system().lower()
   ```

---

## 🧠 **Phase 4 — App Detection & Management**

**Goal:** List installed or running apps.

**Steps:**

1. Use `psutil.process_iter()` to get running apps.
2. Filter out system processes (keep user apps).
3. Display app name + icon (optional) + toggle switch in the GUI list.

---

## 🔐 **Phase 5 — Firewall Logic Integration**

**Goal:** Wire UI to backend.

**Steps:**

1. When user toggles → call `block_app()` or `unblock_app()`
2. Add a small JSON to remember which apps are blocked:

   ```
   data/settings.json
   { "blocked": ["chrome.exe", "spotify.exe"] }
   ```
3. On startup → reapply rules for blocked apps.

---

## 🧰 **Phase 6 — Build & Distribution**

**Goal:** Package the app into standalone executables.

**Steps:**

1. Use PyInstaller:

   ```bash
   pyinstaller --onefile --noconsole main.py
   ```
2. Test `.exe` on Windows & binary on Linux.
3. Optional: add icon using `--icon=icon.ico`.

---

## ✨ **Phase 7 — Polish & Features**

**Ideas:**

* Add system tray icon (toggle global internet lock)
* Add profile modes (“Study Mode”, “Work Mode”)
* Add auto-start on boot (optional)
* Add error logs + permission check for admin mode

---

## 🏁 **End Goal**

A single executable app that:

* Opens instantly
* Lists all apps
* Lets user toggle network access
* Works on both Windows & Linux
* Saves preferences automatically

---