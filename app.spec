# -*- mode: python ; coding: utf-8 -*-
import os
import sys

block_cipher = None

base_dir = os.path.dirname(os.path.abspath(SPEC))
venv_dir = os.path.join(base_dir, 'build_env', 'Lib', 'site-packages')
ort_capi = os.path.join(venv_dir, 'onnxruntime', 'capi')
models_dir = os.path.join(base_dir, 'models')

a = Analysis(
    ['main.py'],
    pathex=[os.path.join(base_dir, 'src')],
    binaries=[],
    datas=[
        (ort_capi, 'onnxruntime/capi'),
        (models_dir, 'models'),
    ],
    hiddenimports=[
        'onnxruntime',
        'onnxruntime.capi',
        'onnxruntime.capi.onnxruntime_pybind11_state',
        'paddleocr',
        'paddleocr.ppocr',
        'paddleocr.ppocr.data',
        'paddleocr.ppocr.modeling',
        'paddleocr.ppocr.postprocess',
        'paddleocr.ppocr.utils',
        'paddlex',
        'paddlex.inference',
        'paddlex.inference.models',
        'dateparser',
        'dateparser.languages',
        'dateparser.date',
        'PIL',
        'numpy',
        'scipy',
        'scipy._cyutility',
        'cv2',
        'flatbuffers',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['rthook_onnxruntime.py'],
    excludes=[
        'paddle',
        'paddlepaddle',
        'torch',
        'tensorflow',
        'tkinter',
        'matplotlib',
        'pytest',
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
    [],
    exclude_binaries=True,
    name='BillRenamer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='BillRenamer',
)
