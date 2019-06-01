import ctypes
from ctypes import wintypes

WH_MOUSE_LL = 14  # 低级鼠标钩子常量
WM_LBUTTONDOWN = 0x0201  # 左键按下事件常量
WM_LBUTTONUP = 0x0202  # 左键回弹事件常量
HC_ACTION = 0

user32 = ctypes.WinDLL('user32', use_last_error=True)

# 定义一些wintypes中没有的类型
ULONG_PTR = wintypes.WPARAM
LRESULT = wintypes.LPARAM
HOOKPROC = ctypes.WINFUNCTYPE(LRESULT, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)
LPMSG = ctypes.POINTER(wintypes.MSG)


# https://msdn.microsoft.com/en-us/library/ms644970
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
# https://docs.microsoft.com/en-us/windows/desktop/api/winuser/nf-winuser-setwindowshookexa
user32.SetWindowsHookExW.restype = wintypes.HHOOK
user32.SetWindowsHookExW.argtypes = (ctypes.c_int, HOOKPROC, wintypes.HINSTANCE, wintypes.DWORD)
# https://docs.microsoft.com/en-us/windows/desktop/api/winuser/nf-winuser-callnexthookex
user32.CallNextHookEx.restype = LRESULT
user32.CallNextHookEx.argtypes = (wintypes.HHOOK, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)
# https://docs.microsoft.com/en-us/windows/desktop/api/winuser/nf-winuser-getmessagew
user32.GetMessageW.restype = wintypes.BOOL
user32.GetMessageW.argtypes = (LPMSG, wintypes.HWND, wintypes.UINT, wintypes.UINT)
# https://docs.microsoft.com/en-us/windows/desktop/api/winuser/nf-winuser-translatemessage
user32.TranslateMessage.restype = wintypes.BOOL
user32.TranslateMessage.argtypes = (LPMSG,)
# https://docs.microsoft.com/en-us/windows/desktop/api/winuser/nf-winuser-dispatchmessagew
user32.DispatchMessageW.restype = LRESULT
user32.DispatchMessageW.argtypes = (LPMSG,)

# 鼠标事件回调函数, wParam是事件类型，lParam是一个MSLLHOOKSTRUCT的结构体，其中包括鼠标坐标等信息
@LowLevelMouseProc
def callback_func(nCode, wParam, lParam):
    if nCode == HC_ACTION:
        if wParam == WM_LBUTTONDOWN:  # 左键按下，解析并记录lParam中的鼠标坐标
            ms_ll_msg = ctypes.cast(lParam, ctypes.POINTER(MSLLHOOKSTRUCT))[0]
            print('左键按下，位于(%d, %d)' % (ms_ll_msg.pt.x, ms_ll_msg.pt.y))
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
