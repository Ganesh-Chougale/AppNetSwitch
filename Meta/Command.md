### Summary  
```bash
node Codex/Runner.js "App"
```  

### Run App in dev mode  
```bash
# for bash
source .venv/Scripts/activate
cd App
python -m app.main
```  
```bash
# for powershelll
.\App\.venv\Scripts\Activate.ps1
cd App
python -m app.main
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
python -m PyInstaller appnetswitch.spec
```  