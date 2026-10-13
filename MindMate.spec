# Build with Build Windows App.bat to isolate Windows DLL search paths.
# Only original visual assets are bundled; keys and journals stay on each user's PC.
from pathlib import Path

project_root = Path(SPECPATH)

a = Analysis(
    [str(project_root / 'MindMate.py')],
    pathex=[str(project_root)],
    binaries=[],
    datas=[(str(project_root / 'Assets'), 'Assets')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PyQt5', 'PySide2', 'PySide6'],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='MindMate',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    icon=str(project_root / 'Assets' / 'icon.ico'),
)
