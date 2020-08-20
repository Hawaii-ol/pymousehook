import ctypes
from ctypes import wintypes

WH_MOUSE_LL = 14  # 低级鼠标钩子常量
WM_LBUTTONDOWN = 0x0201  # 左键按下事件常量
WM_LBUTTONUP = 0x0202  # 左键回弹事件常量
HC_ACTION = 0

user32 = ctypes.WinDLL('user32', use_last_error=True)
gdi32 = ctypes.WinDLL('gdi32', use_last_error=True)

# 定义一些wintypes中没有的类型
ULONG_PTR = wintypes.WPARAM
LRESULT = wintypes.LPARAM
HOOKPROC = ctypes.WINFUNCTYPE(LRESULT, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)
LPMSG = ctypes.POINTER(wintypes.MSG)

class MSLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = (
        ('pt',          wintypes.POINT),
        ('mouseData',   wintypes.DWORD),
        ('flags',       wintypes.DWORD),
        ('time',        wintypes.DWORD),
        ('dwExtraInfo', ULONG_PTR),
    )

'''
https://docs.microsoft.com/en-us/previous-versions/windows/desktop/legacy/ms644986
LowLevelMouseProc回调函数原型：
LRESULT CALLBACK LowLevelMouseProc(
  _In_ int    nCode,
  _In_ WPARAM wParam,
  _In_ LPARAM lParam
);
'''
LowLevelMouseProc = ctypes.WINFUNCTYPE(LRESULT, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)

# 注册user32中的各API参数和返回值
user32.SetWindowsHookExW.restype = wintypes.HHOOK
user32.SetWindowsHookExW.argtypes = (ctypes.c_int, HOOKPROC, wintypes.HINSTANCE, wintypes.DWORD)
user32.CallNextHookEx.restype = LRESULT
user32.CallNextHookEx.argtypes = (wintypes.HHOOK, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)
user32.GetMessageW.restype = wintypes.BOOL
user32.GetMessageW.argtypes = (LPMSG, wintypes.HWND, wintypes.UINT, wintypes.UINT)
user32.TranslateMessage.restype = wintypes.BOOL
user32.TranslateMessage.argtypes = (LPMSG,)
user32.DispatchMessageW.restype = LRESULT
user32.DispatchMessageW.argtypes = (LPMSG,)
user32.GetDC.restype = wintypes.HDC
user32.GetDC.argtypes = (wintypes.HWND,)
user32.ReleaseDC.restype = ctypes.c_int
user32.ReleaseDC.argtypes = (wintypes.HWND, wintypes.HDC)
# 注册GetPixel
gdi32.GetPixel.restype = wintypes.COLORREF
gdi32.GetPixel.argtypes = (wintypes.HDC, ctypes.c_int, ctypes.c_int)

# 鼠标事件回调函数, wParam是事件类型，lParam是一个MSLLHOOKSTRUCT的结构体，其中包括鼠标坐标等信息
@LowLevelMouseProc
def callback_func(nCode, wParam, lParam):
    if nCode == HC_ACTION:
        if wParam == WM_LBUTTONDOWN:  # 左键按下
            # 解析鼠标坐标
            ms_ll_msg = ctypes.cast(lParam, ctypes.POINTER(MSLLHOOKSTRUCT))[0]
            # 获取对应点像素值
            hdc = user32.GetDC(None)
            x, y = ms_ll_msg.pt.x, ms_ll_msg.pt.y
            color = gdi32.GetPixel(hdc, x, y)
            r = color & 0xFF
            g = (color >> 2) & 0xFF
            b = (color >> 4) & 0xFF
            print('coord=(%d,%d), color=#%02X%02X%02X' % (x, y, r, g, b))
            user32.ReleaseDC(None, hdc)
    return user32.CallNextHookEx(None, nCode, wParam, lParam)


# Windows消息循环
def event_loop():
    msg = wintypes.MSG()
    while True:
        bRet = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
        if bRet == 0:  # WM_QUIT消息
            print('bye')
            exit(0)
        elif bRet == -1:  # 错误
            print('an error happened')
            exit(-1)
        else:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))


if __name__ == '__main__':
    # 注册鼠标钩子
    hMouseHook = user32.SetWindowsHookExW(WH_MOUSE_LL, callback_func, None, 0)
    event_loop()
