# -*- mode: python ; coding: utf-8 -*-
import os

a = Analysis(
    ['chrome_automation_tool.py'],
    pathex=[],
    binaries=[],
    datas=[('web', 'web'), ('icon.ico', '.'), ('command.txt', '.')],
    hiddenimports=['utils', 'step_window', 'selenium_handler'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='Chrome自動化工具',
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
    icon='icon.ico',
)
