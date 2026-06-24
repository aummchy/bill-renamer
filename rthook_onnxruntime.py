"""
Runtime hook: preload onnxruntime native DLLs before any Python import can fail.

onnxruntime >= 1.19 introduced onnxruntime.dll which, during its DllMain,
calls LoadLibraryW("onnxruntime_providers_shared.dll") using the standard
Win32 search order -- NOT the AddDllDirectory order. In a one-file
PyInstaller bundle the DLLs land in _MEIPASS/onnxruntime/capi/ which is
NOT covered by SetDllDirectory(_MEIPASS) or PATH.

The fix: load both DLLs by absolute path with ctypes.WinDLL() here, before
Python's importlib ever tries to load the .pyd.
"""
import ctypes
import os
import sys

if sys.platform == "win32" and hasattr(sys, "_MEIPASS"):
    _capi = os.path.join(sys._MEIPASS, "onnxruntime", "capi")
    for _dll in ("onnxruntime_providers_shared.dll", "onnxruntime.dll"):
        _path = os.path.join(_capi, _dll)
        if os.path.isfile(_path):
            ctypes.WinDLL(_path)
    if os.path.isdir(_capi):
        os.add_dll_directory(_capi)
