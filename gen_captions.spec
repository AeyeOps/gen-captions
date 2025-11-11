# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for gen-captions.

This spec file creates a self-contained, single-file executable that includes
all dependencies and can be copied to /opt/bin without requiring sudo.

Build with: pyinstaller gen_captions.spec
Output: dist/gen-captions (single executable file)
"""

import sys
from pathlib import Path

# Get the project root directory
project_root = Path(SPECPATH)
gen_captions_pkg = project_root / 'gen_captions'

# Collect all data files that need to be included
datas = [
    # Provide pyproject.toml so runtime version fallback can read it
    (str(project_root / 'pyproject.toml'), '.'),
    # Include default configuration file
    (str(gen_captions_pkg / 'default.yaml'), 'gen_captions'),
]

# Hidden imports that PyInstaller might miss
hiddenimports = [
    'typer',
    'rich',
    'rich.console',
    'rich.progress',
    'rich.table',
    'yaml',
    'openai',
    'concurrent_log_handler',
    'requests',
    'urllib3',
    # Dedupe dependencies
    'PIL',
    'PIL.Image',
    'imagehash',
    'numpy',
    'scipy',
    'pywt',
]

# Binaries to include (usually auto-detected, but can be specified here)
binaries = []

# Modules to exclude to reduce binary size
excludes = [
    'tkinter',
    'matplotlib',
    'pandas',
    'torch',
    'transformers',
    'pytest',
    'unittest',
    'test',
    'tests',
    'setuptools',
    'distutils',
]

a = Analysis(
    # Entry point script
    ['gen_captions/__main__.py'],
    pathex=[str(project_root)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    # Win32 specific (no effect on Linux)
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    # Cipher for bytecode encryption (None = no encryption)
    cipher=None,
    noarchive=False,
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=None,
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='gen-captions',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,  # Strip symbols to reduce size (Linux/Mac)
    upx=True,  # Use UPX compression if available (reduces size ~50%)
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Console application (not GUI)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # Single file mode - everything bundled into one executable
    onefile=True,
)

# Note: COLLECT and BUNDLE are not needed for onefile mode
# The executable will be placed in dist/gen-captions
