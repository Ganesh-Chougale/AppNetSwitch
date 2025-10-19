# AppNetSwitch - Debug Guide

## Issue: Toggle Clicks Not Being Detected

### Root Cause
The PyQt6 QCheckBox `stateChanged` signal fires **before** the state actually changes, and the `clicked` signal doesn't work well with custom painted checkboxes.

### Solution Implemented
1. **Custom Signal**: Added `userToggled` signal to ToggleSwitch class
2. **Mouse Event Override**: Override `mousePressEvent()` to detect user clicks
3. **State Management**: Use `_user_initiated` flag to distinguish user clicks from programmatic changes
4. **Proper Callback**: Connect `userToggled` signal to `_on_toggle_user_toggled()` method

### Changes Made to `ui_main.py`

#### 1. Added pyqtSignal import
```python
from PyQt6.QtCore import Qt, QRect, QSize, QPropertyAnimation, QEasingCurve, pyqtProperty, pyqtSignal
```

#### 2. Added custom signal to ToggleSwitch
```python
class ToggleSwitch(QCheckBox):
    # Custom signal for user-initiated toggles
    userToggled = pyqtSignal(bool)
```

#### 3. Override mousePressEvent
```python
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
```

#### 4. Connect to userToggled signal in populate_app_list
```python
toggle.userToggled.connect(partial(self._on_toggle_user_toggled, toggle))
```

#### 5. Handle toggle in _on_toggle_user_toggled
```python
def _on_toggle_user_toggled(self, toggle, new_state):
    """Callback for user-initiated toggle changes"""
    print(f"[UI] Toggle clicked for {toggle.app_name}: new_state={new_state}")
    toggle.on_toggle_callback(toggle.app_path, toggle.app_name, new_state)
```

## Expected Debug Output

When you click a toggle, you should see:
```
[DEBUG] ToggleSwitch mousePressEvent detected
[DEBUG] userToggled signal emitted with state=False
[UI] Toggle clicked for chrome.exe: new_state=False (1=allowed, 0=blocked)
[INFO] Toggle: chrome.exe → Block
[DEBUG] Blocking chrome.exe
[DEBUG] Settings saved. Blocked apps: {'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'}
```

## Testing Steps

1. **Run the app as Administrator**
   ```bash
   python App/main.py
   ```

2. **Click on a toggle switch** - You should see debug output in the console

3. **Check the toggle state** - It should turn red (blocked) or green (allowed)

4. **Verify firewall rule** - Check Windows Firewall:
   ```bash
   netsh advfirewall firewall show rule name=all | findstr AppNetSwitch
   ```

5. **Check settings file** - Verify `data/settings.json` is updated:
   ```json
   {
     "blocked": ["C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"]
   }
   ```

## If It Still Doesn't Work

1. **Check console for errors** - Look for any exception messages
2. **Verify admin rights** - Run as Administrator
3. **Test toggle isolation** - Run `test_toggle.py` to test the toggle in isolation
4. **Check firewall permissions** - Ensure you can run netsh commands manually

## Console Commands to Test Manually

```bash
# List all AppNetSwitch rules
netsh advfirewall firewall show rule name=all | findstr AppNetSwitch

# Add a test rule
netsh advfirewall firewall add rule name="TestRule" dir=out action=block program="C:\Windows\System32\notepad.exe" enable=yes

# Delete the test rule
netsh advfirewall firewall delete rule name="TestRule"
```
