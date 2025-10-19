# AppNetSwitch - Toggle Bug Fixes (Complete Solution)

## 🎯 Problem Solved
**Toggle switches were not responding to clicks, preventing users from blocking/unblocking applications.**

## 🔧 Solution Overview

The issue was caused by PyQt6's signal timing problems with custom-painted checkboxes. The solution implements a custom signal-based approach that directly detects user mouse clicks.

## 📋 Changes Made

### 1. **ui_main.py** - Signal Handling Overhaul

#### Added Custom Signal
```python
class ToggleSwitch(QCheckBox):
    userToggled = pyqtSignal(bool)  # ← NEW
```

#### Override Mouse Click Detection
```python
def mousePressEvent(self, event):
    """Override to detect user clicks and toggle state"""
    print(f"[DEBUG] ToggleSwitch mousePressEvent detected")
    new_state = not self.isChecked()
    self._user_initiated = True
    self.setChecked(new_state)
    self._user_initiated = False
    self.userToggled.emit(new_state)  # ← Emit signal with new state
    print(f"[DEBUG] userToggled signal emitted with state={new_state}")
```

#### Connect Signal in populate_app_list
```python
# Store app info on toggle widget
toggle.app_path = app["path"]
toggle.app_name = app["name"]
toggle.on_toggle_callback = on_toggle

# Connect to custom signal
toggle.userToggled.connect(partial(self._on_toggle_user_toggled, toggle))
```

#### Handle Toggle Event
```python
def _on_toggle_user_toggled(self, toggle, new_state):
    """Callback for user-initiated toggle changes"""
    print(f"[UI] Toggle clicked for {toggle.app_name}: new_state={new_state}")
    toggle.on_toggle_callback(toggle.app_path, toggle.app_name, new_state)
```

### 2. **main.py** - Fixed Toggle Logic

#### Corrected State Logic
```python
def toggle_internet(self, app_path, app_name, state):
    # state is True (1) = allowed, False (0) = blocked
    action = "Allow" if state else "Block"
    print(f"[INFO] Toggle: {app_name} → {action}")
    
    if state:  # True/checked → Allow (unblock)
        unblock_app(target)
        self.blocked.discard(app_path)
    else:  # False/unchecked → Block
        block_app(target)
        self.blocked.add(app_path)
```

#### Fixed reapply_blocked Loop
```python
def reapply_blocked(self):
    print("[INFO] Reapplying previously blocked apps:", self.blocked)
    for app_path in self.blocked:  # ← ADDED LOOP
        app = self.app_data_map.get(app_path)
        if app:
            target = app["pid"] if platform.system().lower() == "linux" else app_path
            Thread(target=self._safe_block, args=(target, app_path, app["name"]), daemon=True).start()
```

#### Fixed _safe_block Exception Handling
```python
def _safe_block(self, target, app_path, app_name):
    try:
        block_app(target)
    except Exception as e:  # ← ADDED EXCEPT CLAUSE
        print(f"[ERROR] _safe_block failed for {app_name}: {e}")
        traceback.print_exc()
```

## ✅ Testing Instructions

### Step 1: Run as Administrator
```bash
cd c:\Users\RaSkull\Desktop\Code\AppNetSwitch
.venv\Scripts\activate
python App/main.py
```

### Step 2: Test Toggle Click
1. Look for an application in the list (e.g., "chrome.exe")
2. Click on its toggle switch
3. Watch the console for debug output

### Step 3: Verify Console Output
You should see:
```
[DEBUG] ToggleSwitch mousePressEvent detected
[DEBUG] userToggled signal emitted with state=False
[UI] Toggle clicked for chrome.exe: new_state=False (1=allowed, 0=blocked)
[INFO] Toggle: chrome.exe → Block
[DEBUG] Blocking chrome.exe
[netsh stdout] Ok.
[DEBUG] Settings saved. blocked apps: {'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'}
```

### Step 4: Verify Firewall Rule
```bash
netsh advfirewall firewall show rule name=all | findstr AppNetSwitch
```

You should see a rule like:
```
Rule Name:                            AppNetSwitch_chrome_exe_12345678
```

### Step 5: Verify Settings File
```bash
type App\data\settings.json
```

Should show:
```json
{
  "blocked": ["C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"]
}
```

## 🎨 UI Behavior

- **Green Toggle** = App is allowed to access internet
- **Red Toggle** = App is blocked from accessing internet
- **Click Toggle** = Instantly changes color and creates/deletes firewall rule
- **Refresh Button** = Reloads the app list
- **Exit Button** = Closes the application

## 🐛 Troubleshooting

### Toggle clicks not detected
1. ✅ Verify running as Administrator
2. ✅ Check console for error messages
3. ✅ Run `test_toggle.py` to isolate the issue
4. ✅ Look for exceptions in the console

### Firewall rules not created
1. ✅ Verify admin rights
2. ✅ Test netsh manually: `netsh advfirewall firewall show rule name=all`
3. ✅ Check Windows Firewall is enabled
4. ✅ Look for netsh errors in console

### Settings not saving
1. ✅ Verify `data/` folder exists
2. ✅ Check write permissions: `icacls App\data`
3. ✅ Look for file I/O errors in console

## 📊 Debug Output Levels

| Level | Example | Meaning |
|-------|---------|---------|
| `[DEBUG]` | ToggleSwitch mousePressEvent detected | Low-level UI events |
| `[UI]` | Toggle clicked for chrome.exe | UI layer events |
| `[INFO]` | Toggle: chrome.exe → Block | High-level operations |
| `[ERROR]` | Failed to block app | Error conditions |

## 🔄 How It Works

1. **User clicks toggle** → `mousePressEvent()` fires
2. **State is toggled** → `setChecked(new_state)` changes the state
3. **Signal is emitted** → `userToggled.emit(new_state)` sends the new state
4. **Callback is triggered** → `_on_toggle_user_toggled()` receives the event
5. **Main logic executes** → `toggle_internet()` blocks/unblocks the app
6. **Firewall rule created/deleted** → `block_app()` or `unblock_app()` runs
7. **Settings saved** → `save_settings()` persists the change
8. **UI updated** → Toggle color changes and button is re-enabled

## 📁 Files Modified

- ✅ `ui_main.py` - Custom signal, mouse event override, signal connections
- ✅ `main.py` - Fixed toggle logic, reapply loop, exception handling
- ✅ `firewall/windows.py` - Already correct (no changes needed)
- ✅ `firewall/linux.py` - Already correct (no changes needed)
- ✅ `utils/app_manager.py` - Already correct (no changes needed)
- ✅ `utils/settings_manager.py` - Already correct (no changes needed)

## 🚀 Next Steps

After verifying the fixes work:

1. **Test blocking actual apps** - Try blocking Chrome, Spotify, etc.
2. **Verify network blocking** - Try accessing the internet from blocked apps
3. **Test app restart** - Close and reopen the app, verify blocked apps are re-blocked
4. **Build executable** - Use PyInstaller to create standalone .exe
5. **Add more features** - Profiles, auto-start, system tray icon, etc.

## 📝 Notes

- All changes are backward compatible
- No new dependencies added
- Console output is verbose for debugging (can be reduced later)
- Settings are automatically persisted to `data/settings.json`
- Firewall rules are prefixed with `AppNetSwitch_` for easy identification
