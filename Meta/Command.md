### Summary  
```bash
node Codex/Runner.js "App"
```  

### Run App in dev mode  
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

### Git Pushes
```bash
git add .
git commit -m "message"
git push origin main
```  

### Create app
#### Windows  
```bash
source ./App/.venv/Scripts/activate
cd App
# python -m PyInstaller --name "AppNetSwitch" --onefile --noconsole --icon="Extras/File_Icon.ico" main.py
python -m PyInstaller appnetswitch.spec
```  