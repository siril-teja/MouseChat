import time
import ctypes
import comtypes.client
import win32clipboard

# Virtual-key codes
VK_CONTROL = 0x11
VK_MENU    = 0x12  # Alt
VK_SHIFT   = 0x10
VK_C       = 0x43
KEYEVENTF_KEYUP = 0x0002

user32 = ctypes.windll.user32
GetAsyncKeyState = user32.GetAsyncKeyState

def _key_is_down(vk):
    return (GetAsyncKeyState(vk) & 0x8000) != 0

def _key_down(vk):
    user32.keybd_event(vk, 0, 0, 0)

def _key_up(vk):
    user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)

def _clipboard_get():
    CF_UNICODETEXT = 13
    text = ""
    win32clipboard.OpenClipboard()
    try:
        if win32clipboard.IsClipboardFormatAvailable(CF_UNICODETEXT):
            text = win32clipboard.GetClipboardData(CF_UNICODETEXT)
    finally:
        win32clipboard.CloseClipboard()
    return text or ""

def _clipboard_set(text: str):
    win32clipboard.OpenClipboard()
    try:
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardText(text)
    finally:
        win32clipboard.CloseClipboard()

def get_selected_text_uia() -> str:
    try:
        uia = comtypes.client.CreateObject('UIAutomationClient.CUIAutomation8')
        focused = uia.GetFocusedElement()
        if not focused:
            return ""
        TEXT_PATTERN_ID = 10024
        try:
            pattern = focused.GetCurrentPattern(TEXT_PATTERN_ID)
        except Exception:
            return ""
        if not pattern:
            return ""
        ranges = pattern.GetSelection()
        if not ranges:
            return ""
        texts = []
        for i in range(ranges.Length):
            try:
                texts.append(ranges.GetElement(i).GetText(-1))
            except Exception:
                pass
        return "\n".join([t for t in texts if t]).strip()
    except Exception:
        return ""

def get_selected_text_clipboard_safe() -> str:
    """
    Fallback: momentarily release Alt/Shift, send Ctrl+C, read clipboard,
    restore clipboard and key state. Only return if clipboard changed.
    """
    before = ""
    try:
        before = _clipboard_get()
    except Exception:
        pass

    # Remember modifier state
    alt_was_down = _key_is_down(VK_MENU)
    shift_was_down = _key_is_down(VK_SHIFT)

    # Ensure clean modifiers for copy
    if alt_was_down:  _key_up(VK_MENU)
    if shift_was_down: _key_up(VK_SHIFT)

    # Send Ctrl+C
    _key_down(VK_CONTROL)
    _key_down(VK_C)
    _key_up(VK_C)
    _key_up(VK_CONTROL)

    time.sleep(0.10)  # let target app update clipboard

    after = ""
    try:
        after = _clipboard_get()
    except Exception:
        after = ""

    # Restore prior modifier state
    if shift_was_down: _key_down(VK_SHIFT)
    if alt_was_down:   _key_down(VK_MENU)

    # Restore original clipboard
    try:
        _clipboard_set(before)
    except Exception:
        pass

    if not after or after == before:
        return ""
    return after.strip()

def get_selected_text() -> str:
    txt = get_selected_text_uia().strip()
    if txt:
        return txt
    return get_selected_text_clipboard_safe()
