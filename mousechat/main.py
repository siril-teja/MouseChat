# mousechat/main.py
from PyQt6 import QtWidgets, QtCore, QtGui
from pynput import keyboard
from pynput.keyboard import Key, KeyCode
from mousechat.selection import get_selected_text
from mousechat.chatwin import open_chat, ChatWin
from mousechat.llm import ask_llm
import threading
import time
import inspect

APP_ORG = "MouseChat"
APP_NAME = "MouseChatDesktop"

# Hotkey: Alt+Q. If you prefer Ctrl+Q, swap to the commented line.
HOTKEY = {Key.alt_l, KeyCode.from_char('q')}
# HOTKEY = {Key.ctrl_l, KeyCode.from_char('q')}

DEFAULT_MODELS = [
    "openai/chatgpt-5",  # your preferred default
    "openai/gpt-4o-mini",
    "openai/gpt-4o",
    "openai/gpt-4.1-mini",
    "anthropic/claude-3.5-sonnet",
    "google/gemini-1.5-pro",
]

def _llm_call(prompt: str, model: str) -> str:
    """Call ask_llm. If it supports (prompt, model), use it; else fallback to (prompt) only."""
    try:
        sig = inspect.signature(ask_llm)
        if len(sig.parameters) >= 2:
            return ask_llm(prompt, model)  # type: ignore
    except Exception:
        pass
    return ask_llm(prompt)

class LLMWorker(QtCore.QObject):
    finished = QtCore.pyqtSignal(str)
    failed = QtCore.pyqtSignal(str)
    def __init__(self, prompt: str, model: str):
        super().__init__()
        self.prompt = prompt
        self.model = model
    @QtCore.pyqtSlot()
    def run(self):
        try:
            ans = _llm_call(self.prompt, self.model)
            self.finished.emit(ans if ans is not None else "")
        except Exception as e:
            self.failed.emit(f"Error calling model: {e}")

class AppController(QtCore.QObject):
    def __init__(self, app: QtWidgets.QApplication):
        super().__init__()
        self.app = app
        self.settings = QtCore.QSettings(APP_ORG, APP_NAME)

        self.models = DEFAULT_MODELS[:]
        self.current_model = self.settings.value("current_model", self.models[0])
        if self.current_model not in self.models:
            self.current_model = self.models[0]

        self.chat: ChatWin | None = None

    @QtCore.pyqtSlot()
    def on_hotkey(self):
        # Toggle the chat window
        if self.chat is not None and self.chat.isVisible():
            self.chat.close()
            self.chat = None
            return

        # let Alt release before reading selection
        QtCore.QTimer.singleShot(120, self._open_with_selection)

    def _open_with_selection(self):
        prefill = get_selected_text()
        self.chat = self._open_chat_with_model(prefill)

    def _open_chat_with_model(self, prefill: str) -> ChatWin:
        def on_send(window: ChatWin, prompt: str):
            window.setBusy(True)
            # worker thread for the LLM call
            thread = QtCore.QThread(parent=window)
            worker = LLMWorker(prompt, self.current_model)
            worker.moveToThread(thread)
            thread.started.connect(worker.run)
            worker.finished.connect(lambda ans: self._finish_ok(window, thread, worker, ans))
            worker.failed.connect(lambda err: self._finish_err(window, thread, worker, err))
            worker.finished.connect(thread.quit)
            worker.failed.connect(thread.quit)
            thread.finished.connect(thread.deleteLater)
            thread.start()

        # Create & show the chat window
        w = open_chat(prefill, on_send)  # shows and returns ChatWin
        w.setModels(self.models, self.current_model)
        w.modelChanged.connect(self._on_model_changed)
        w.updateTitleWithModel(self.current_model)

        # Place near cursor
        pos = QtGui.QCursor.pos()
        w.move(pos.x() + 16, pos.y() + 16)
        w.raise_()
        w.activateWindow()
        return w

    @QtCore.pyqtSlot(str)
    def _on_model_changed(self, model: str):
        self.current_model = model
        self.settings.setValue("current_model", model)
        if self.chat is not None:
            self.chat.updateTitleWithModel(model)

    @QtCore.pyqtSlot()
    def _finish_ok(self, window, thread, worker, ans: str):
        window.setResponse(ans)
        window.setBusy(False)

    @QtCore.pyqtSlot()
    def _finish_err(self, window, thread, worker, err: str):
        window.setResponse(err)
        window.setBusy(False)

def start_hotkey_listener(controller: AppController):
    combo = set()
    last_fire = 0.0
    def fire():
        QtCore.QMetaObject.invokeMethod(
            controller, "on_hotkey", QtCore.Qt.ConnectionType.QueuedConnection
        )
    def on_press(k):
        nonlocal last_fire
        if k in HOTKEY:
            combo.add(k)
            if HOTKEY.issubset(combo):
                now = time.time()
                if now - last_fire > 0.3:
                    last_fire = now
                    fire()
    def on_release(k):
        combo.discard(k)
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()

if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    app.setOrganizationName(APP_ORG)
    app.setApplicationName(APP_NAME)

    controller = AppController(app)
    controller.moveToThread(app.thread())

    t_hotkey = threading.Thread(target=start_hotkey_listener, args=(controller,), daemon=True)
    t_hotkey.start()

    app.exec()
