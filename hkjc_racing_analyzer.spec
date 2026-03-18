# -*- mode: python ; coding: utf-8 -*-

import sys
import os

block_cipher = None

# Get the current directory
base_dir = os.path.abspath('.')

a = Analysis(
    ['main.py'],
    pathex=[base_dir],
    binaries=[],
    datas=[
        ('database', 'database'),
        ('i18n', 'i18n'),
        ('loading.jpg', '.'),
        ('drivers/chromedriver', 'drivers'),
    ],
    hiddenimports=[
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'pandas',
        'numpy',
        'sklearn',
        'sklearn.ensemble',
        'sklearn.tree',
        'sklearn.linear_model',
        'sqlite3',
        'engine',
        'engine.core',
        'engine.features',
        'engine.models',
        'engine.prediction',
        'engine.live',
        'engine.verification',
        'ui',
        'scraper',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='HKJC_Racing_Analyzer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to True for debugging
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add path to .ico file if you have one
)

# For macOS, create an app bundle
if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='HKJC_Racing_Analyzer.app',
        icon=None,
        bundle_identifier='com.hkjc.racinganalyzer',
    )
