# AppNetSwitch - Row Highlighting Feature

## What Was Implemented

Combined **Option 1 (Hover Highlight)** + **Option 3 (Alternating Row Colors)** for the best user experience.

## Visual Guide

### Normal State (No Hover)
```
┌────────────────────────────────────────────────────────┐
│ 🖥 chrome.exe                                [●  ]    │ ← White background
├────────────────────────────────────────────────────────┤
│ 🖥 firefox.exe                               [  ●]   │ ← Light gray background
├────────────────────────────────────────────────────────┤
│ 🖥 spotify.exe                               [●  ]   │ ← White background
├────────────────────────────────────────────────────────┤
│ 🖥 vlc.exe                                   [  ●]   │ ← Light gray background
└────────────────────────────────────────────────────────┘
```

### When You Hover Over a Row
```
┌────────────────────────────────────────────────────────┐
│ 🖥 chrome.exe                                [●  ]    │ ← Normal (white)
├────────────────────────────────────────────────────────┤
│ 🖥 firefox.exe                               [  ●]   │ ← HOVER (darker gray)
├────────────────────────────────────────────────────────┤
│ 🖥 spotify.exe                               [●  ]   │ ← Normal (white)
├────────────────────────────────────────────────────────┤
│ 🖥 vlc.exe                                   [  ●]   │ ← Light gray background
└────────────────────────────────────────────────────────┘
```

## Color Scheme

| State | Even Rows (0,2,4...) | Odd Rows (1,3,5...) |
|-------|----------------------|---------------------|
| Normal | `#FFFFFF` (White) | `#F5F5F5` (Light Gray) |
| Hover | `#E8E8E8` (Gray) | `#EBEBEB` (Gray) |

## Benefits

✅ **Always Clear** - Alternating colors make it obvious which toggle belongs to which app
✅ **Interactive Feedback** - Hover effect shows which row you're about to interact with
✅ **Professional Look** - Table-like appearance is familiar to users
✅ **No Performance Impact** - Simple CSS styling
✅ **Works at Any Size** - Scales with window resizing and maximizing

## How It Works

1. **Alternating Colors:**
   - Even-indexed rows (0, 2, 4...) get white background
   - Odd-indexed rows (1, 3, 5...) get light gray background
   - Creates a zebra-stripe pattern for clarity

2. **Hover Highlighting:**
   - When mouse enters a row, background becomes darker gray
   - When mouse leaves, background returns to original color
   - Provides visual feedback that the row is interactive

3. **Smooth Transitions:**
   - Color changes instantly (no animation needed)
   - Works with toggle clicks and other interactions

## Testing

1. **Run the app:**
   ```bash
   python App/main.py
   ```

2. **Look at the app list:**
   - Notice alternating white and light gray rows
   - Each app name and toggle are clearly grouped together

3. **Hover over rows:**
   - Move your mouse over different app rows
   - Notice the background gets slightly darker
   - Move mouse away - color returns to normal

4. **Click toggles:**
   - Hover effect helps you see which toggle you're about to click
   - Click to block/unblock the app

## Code Implementation

### Alternating Colors
```python
if index % 2 == 0:
    row_widget.setStyleSheet("QWidget { background-color: #FFFFFF; }")
else:
    row_widget.setStyleSheet("QWidget { background-color: #F5F5F5; }")
```

### Hover Effect
```python
def _on_row_enter(self, row_widget):
    """Highlight on hover"""
    if row_widget.is_even:
        row_widget.setStyleSheet("QWidget { background-color: #E8E8E8; }")
    else:
        row_widget.setStyleSheet("QWidget { background-color: #EBEBEB; }")

def _on_row_leave(self, row_widget):
    """Restore original color"""
    row_widget.setStyleSheet(row_widget.original_stylesheet)
```

## Future Enhancements

- Add smooth color transitions with CSS animations
- Add icons to show app status (blocked/allowed)
- Add right-click context menu for more options
- Add search/filter to find apps quickly
- Add sorting options (by name, status, etc.)
