import ctypes

class _CursorInfo(ctypes.Structure):
    _fields_ = [('size', ctypes.c_int), ('visible', ctypes.c_byte)]

def set_cursor_visible(visible, size=-1):
    ci = _CursorInfo()
    handle = ctypes.windll.kernel32.GetStdHandle(-11)
    ctypes.windll.kernel32.GetConsoleCursorInfo(handle, ctypes.byref(ci))
    ci.visible = visible
    if size >= 0:
        ci.size = size
    ctypes.windll.kernel32.SetConsoleCursorInfo(handle, ctypes.byref(ci))