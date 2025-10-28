# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['app/main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('app/ui/resources/File_Icon.ico', 'app/ui/resources'),
        ('app/ui/resources/File_Icon.png', 'app/ui/resources'),
        ('app/ui/resources/loading.svg', 'app/ui/resources'),
        ('app/data/settings.json', 'app/data'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'PyQt6.QtWebEngineWidgets', 'PyQt6.QtWebEngineCore', 'PyQt6.QtWebEngine',
        'matplotlib', 'numpy', 'pandas', 'scipy', 'PIL', 'pillow',
        'tkinter', 'unittest', 'email', 'http', 'xml', 'pydoc'
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='AppNetSwitch',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['app/ui/resources/File_Icon.ico'],
    version='app/ui/resources/version_info.txt',
)
