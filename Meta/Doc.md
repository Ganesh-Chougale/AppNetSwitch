### 1. Create python enivornment  
```bash
python -m venv ./App/.venv
```  
```bash
source ./App/.venv/Scripts/activate
# or `.venv/Scripts/Activate.ps1` if PowerShell
```  
### 2. Install dependancies  
```bash
pip install pyqt6 psutil pyinstaller
```  
```bash
# Verify installation
python -m PyQt6.QtCore
pip list
```  