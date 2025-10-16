# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for eBL Photo Stitcher.
This builds a single executable with all required dependencies.

IMPORTANT: CairoSVG Dependencies
--------------------------------
CairoSVG requires the Cairo graphics library DLLs to be present.
On Windows, you need to install GTK3 runtime or ensure libcairo-2.dll is available.

Installation options:
1. Install GTK3 runtime from: https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer
2. Or install via pip: pip install cairosvg[png]
3. Or manually place libcairo-2.dll in your Python site-packages/cairocffi/ directory

This spec file attempts to automatically collect Cairo DLLs from your Python environment.
"""

from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs, collect_submodules
from PyInstaller.utils.hooks import get_hook_config
import os
import sys

pyexiv2_datas = []
pyexiv2_hiddenimports = []
try:
    pyexiv2_datas = collect_data_files('pyexiv2')
except ImportError:
    pass

cairosvg_datas = []
cairosvg_binaries = []
cairosvg_hiddenimports = []
try:
    cairosvg_datas = collect_data_files('cairosvg')
    cairosvg_binaries = collect_dynamic_libs('cairosvg')
    cairosvg_hiddenimports = collect_submodules('cairosvg')
except ImportError:
    pass

cairocffi_binaries = []
try:
    cairocffi_binaries = collect_dynamic_libs('cairocffi')
except ImportError:
    pass

cairo_binaries = []
try:
    import cairocffi
    cairo_lib_path = cairocffi.cairo._lib._name
    if cairo_lib_path and os.path.exists(cairo_lib_path):
        cairo_binaries.append((cairo_lib_path, '.'))
except Exception:
    pass

if sys.platform == 'win32':
    try:
        import site
        site_packages = site.getsitepackages()
        for sp in site_packages:
            cairo_dll_path = os.path.join(sp, 'cairocffi', 'libcairo-2.dll')
            if os.path.exists(cairo_dll_path):
                cairo_binaries.append((cairo_dll_path, '.'))
                break
    except Exception:
        pass

block_cipher = None

a = Analysis(
    ['gui_app.py'],
    pathex=['./lib'],
    binaries=[] + cairosvg_binaries + cairocffi_binaries + cairo_binaries,
    datas=[
        ('assets', 'assets'),
        ('lib', 'lib'),
    ] + pyexiv2_datas + cairosvg_datas,
    hiddenimports=[
        'cv2', 
        'numpy',
        'imageio',
        'rawpy',
        'piexif',
        'pyexiv2',
        'cairosvg',
        'cairosvg.surface',
        'cairosvg.parser',
        'cairosvg.css',
        'cairosvg.features',
        'cairosvg.helpers',
        'cairosvg.url',
        'cairocffi',
        'cairocffi.pixbuf',
        'cairocffi.constants',
        'cairocffi.ffi',
        'cffi',
        'tinycss2',
        'cssselect2',
        'defusedxml',
        'webencodings',
        'rembg',
        'onnxruntime',
    ] + pyexiv2_hiddenimports + cairosvg_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

excluded_binaries = [
    'opengl32sw.dll',
    'VCRUNTIME140.dll',
    'MSVCP140.dll',
    'api-ms-win-core*.dll',
    'api-ms-win-crt*.dll',
    'opencv_videoio_ffmpeg*.dll',
    'libopenblas*.dll',
]

a.binaries = TOC([x for x in a.binaries if not any(
    excluded in x[0] for excluded in excluded_binaries)])

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='eBL Photo Stitcher',
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
    icon='eBL_Logo.ico',
)
