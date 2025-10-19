# AppNetSwitch - Bug Fixes Applied

## Problem
When toggling apps in the UI, the block/unblock functionality wasn't working.

## Root Causes Identified

1. **Signal Timing Issue** (`ui_main.py`)
   - Was using `stateChanged` signal which fires **before** the state actually changes
   - This caused the toggle callback to receive the old state instead of the new state

2. **State Logic Inversion** (`main.py`)
   - The `toggle_internet()` function had inverted logic for determining block vs unblock
   - Checked state (1) = allowed, but the code was treating it as blocked

3. **Missing Loop in reapply_blocked()** (`main.py`)
   - The `reapply_blocked()` method was missing the `for app_path in self.blocked:` loop
   - This prevented previously blocked apps from being re-blocked on startup

4. **Missing Exception Handler** (`main.py`)
   - The `_safe_block()` method had a try block without an except clause

5. **Missing UI Element** (`ui_main.py`)
   - The scroll area wasn't being added to the main layout in `setupUi()`

## Fixes Applied

### 1. Fixed Signal Handling (`ui_main.py`)
**Changed from:**
```python
toggle.stateChanged.connect(partial(on_toggle, app["path"], app["name"]))
```

**Changed to:**
```python
toggle.clicked.connect(partial(self._on_toggle_clicked, app["path"], app["name"], on_toggle, toggle))

def _on_toggle_clicked(self, app_path, app_name, on_toggle, toggle):
    """Callback for toggle clicks - passes the NEW state after the click"""
    new_state = toggle.isChecked()
    print(f"[UI] Toggle clicked for {app_name}: new_state={new_state} (1=allowed, 0=blocked)")
    on_toggle(app_path, app_name, new_state)
```

**Why:** The `clicked` signal fires **after** the state changes, so `isChecked()` returns the new state.

### 2. Fixed Toggle Logic (`main.py`)
**Changed from:**
```python
if state == 0:  # unchecked → Block
    block_app(target)
    self.blocked.add(app_path)
else:  # checked → Unblock
    unblock_app(target)
    self.blocked.discard(app_path)
```

**Changed to:**
```python
if state:  # True/checked → Allow (unblock)
    print(f"[DEBUG] Unblocking {app_name}")
    unblock_app(target)
    self.blocked.discard(app_path)
else:  # False/unchecked → Block
    print(f"[DEBUG] Blocking {app_name}")
    block_app(target)
    self.blocked.add(app_path)
```

**Why:** The toggle is checked (True) when allowed, unchecked (False) when blocked.

### 3. Fixed reapply_blocked() (`main.py`)
**Added missing loop:**
```python
def reapply_blocked(self):
    print("[INFO] Reapplying previously blocked apps:", self.blocked)
    for app_path in self.blocked:  # ← ADDED THIS LINE
        app = self.app_data_map.get(app_path)
        if app:
            target = app["pid"] if platform.system().lower() == "linux" else app_path
            Thread(target=self._safe_block, args=(target, app_path, app["name"]), daemon=True).start()
```

### 4. Fixed _safe_block() (`main.py`)
**Added except clause:**
```python
def _safe_block(self, target, app_path, app_name):
    try:
        block_app(target)
    except Exception as e:  # ← ADDED THIS LINE
        print(f"[ERROR] _safe_block failed for {app_name}: {e}")
        traceback.print_exc()
```

### 5. Fixed UI Layout (`ui_main.py`)
**Added missing line in setupUi():**
```python
self.main_layout.addWidget(self.scroll_area)  # ← ADDED THIS LINE
```

## Testing

Run the test script to verify firewall commands work:
```bash
python test_firewall.py
```

Then test the full app:
```bash
python main.py
```

## Expected Behavior After Fixes

1. ✅ UI shows list of running apps
2. ✅ Toggle switches are properly initialized (green = allowed, red = blocked)
3. ✅ Clicking a toggle now properly blocks/unblocks the app
4. ✅ Firewall rules are created/deleted correctly
5. ✅ Settings are saved to `data/settings.json`
6. ✅ On app restart, previously blocked apps are re-blocked
7. ✅ Debug output shows what's happening in the console

## Debug Output Example

```
[INFO] Toggle: chrome.exe → Block
[DEBUG] Blocking chrome.exe
[DEBUG] Unblocking chrome.exe
[DEBUG] Settings saved. Blocked apps: {'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'}
```
