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
pip install pyqt6 psutil pyinstaller Pillow
```  
```bash
# Verify installation
python -m PyQt6.QtCore
pip list
```  

### 3. Code Summary  
```bash
node Codex/Runner.js "App"
```  

### 4. Run App in dev mode  
```bash
# for bash
source ./App/.venv/Scripts/activate
python ./App/main.py 
```  
```bash
# for powershelll
.\App\.venv\Scripts\Activate.ps1
python ./App/main.py 
```  

### 5. Create app
#### Windows  
```bash
source ./App/.venv/Scripts/activate
cd App
# python -m PyInstaller --name "AppNetSwitch" --onefile --noconsole --icon="Extras/File_Icon.ico" main.py
python -m PyInstaller appnetswitch.spec
```  

### Git Pushes
```bash
git add .
git commit -m "message"
git push origin main
```  