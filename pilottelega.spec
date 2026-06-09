# -*- mode: python ; coding: utf-8 -*-
"""Configuration PyInstaller — produit un `.exe` autonome Windows (jalon 5).

Build : `pyinstaller pilottelega.spec --noconfirm`
Résultat : `dist/Pilottelega.exe` (onefile, sans console).
Aucun secret n'est embarqué : identifiants et session restent en local (%APPDATA%).
"""

a = Analysis(
    ["pilottelega/__main__.py"],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=["qasync"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="Pilottelega",
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
)
