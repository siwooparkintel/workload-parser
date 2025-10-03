# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for building wlparser.exe standalone executable.

Usage:
    pyinstaller wlparser.spec

This creates a single executable with all dependencies bundled.
"""

import sys
from pathlib import Path

block_cipher = None

# Get the path to the project root
project_root = Path.cwd()

a = Analysis(
    ['wlparser.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        # Include config files
        ('config/*.json', 'config'),
    ],
    hiddenimports=[
        'tkinter',
        'tkinter.filedialog',
        'pandas',
        'openpyxl',
        'openpyxl.cell._writer',
        'workload_parser',
        'workload_parser.core',
        'workload_parser.core.parser',
        'workload_parser.core.config',
        'workload_parser.core.enhanced_config',
        'workload_parser.core.exceptions',
        'workload_parser.parsers',
        'workload_parser.parsers.power_parser',
        'workload_parser.parsers.socwatch_parser',
        'workload_parser.parsers.etl_parser',
        'workload_parser.parsers.hobl_parser',
        'workload_parser.parsers.intel_parsers',
        'workload_parser.utils',
        'workload_parser.utils.logger',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'scipy',
        'numpy.random._examples',
        'IPython',
        'notebook',
        'jupyter',
        'PIL',
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6',
    ],
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
    name='wlparser',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Keep console window for output
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # You can add an icon file here if you have one
)
