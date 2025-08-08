# mousechat/chatwin.py
from PyQt6 import QtCore, QtGui, QtWidgets
import json

APP_ORG = "MouseChat"
APP_NAME = "MouseChatDesktop"
HISTORY_KEY = "prompt_history"
HISTORY_MAX = 50
THEME_KEY = "theme"  # "dark" or "light"

# ---------- Themes (QSS) ----------
DARK_THEME_QSS = """
#RootFrame {
    background-color: #1e1f22;
    border-radius: 14px;
    border: 1px solid #2a2b2e;
}
QLabel, QToolButton, QPushButton, QComboBox, QPlainTextEdit, QTextEdit {
    font-family: "Segoe UI", sans-serif;
    font-size: 10.5pt;
    color: #e6e6e6;
}
QPlainTextEdit, QTextEdit {
    background-color: #232428;
    border: 1px solid #2f3136;
    border-radius: 8px;
    padding: 8px;
}
QPushButton {
    background-color: #2b2d31;
    border: 1px solid #3a3d43;
    border-radius: 10px;
    padding: 6px 12px;
}
QPushButton:hover { background-color: #34373d; }
QPushButton:pressed { background-color: #25272b; }
QPushButton:disabled { color: rgba(230,230,230,120); }
QComboBox {
    background-color: #232428;
    border: 1px solid #2f3136;
    border-radius: 8px;
    padding: 4px 8px;
}
QComboBox QAbstractItemView {
    background-color: #232428;
    color: #e6e6e6;
    selection-background-color: #34373d;
    border: 1px solid #2f3136;
}
QToolButton {
    background-color: transparent;
    border: none;
    padding: 4px 6px;
    border-radius: 8px;
}
QToolButton:hover { background-color: rgba(255,255,255,0.06); }
"""

LIGHT_THEME_QSS = """
#RootFrame {
    background-color: #f7f8fb;
    border-radius: 14px;
    border: 1px solid #dfe3ea;
}
QLabel, QToolButton, QPushButton, QComboBox, QPlainTextEdit, QTextEdit {
    font-family: "Segoe UI", sans-serif;
    font-size: 10.5pt;
    color: #202124;
}
QPlainTextEdit, QTextEdit {
    background-color: #ffffff;
    border: 1px solid #d0d5dd;
    border-radius: 8px;
    padding: 8px;
}
QPushButton {
    background-color: #ffffff;
    border: 1px solid #d0d5dd;
    border-radius: 10px;
    padding: 6px 12px;
}
QPushButton:hover { background-color: #f0f2f6; }
QPushButton:pressed { background-color: #e7e9ef; }
QPushButton:disabled { color: rgba(32,33,36,140); }
QComboBox {
    background-color: #ffffff;
    border: 1px solid #d0d5dd;
    border-radius: 8px;
    padding: 4px 8px;
}
QComboBox QAbstractItemView {
    background-color: #ffffff;
    color: #202124;
    selection-background-color: #e7e9ef;
    border: 1px solid #d0d5dd;
}
QToolButton {
    background-color: transparent;
    border: none;
    padding: 4px 6px;
    border-radius: 8px;
}
QToolButton:hover { background-color: rgba(0,0,0,0.06); }
"""

class HistoryPlainTextEdit(QtWidgets.QPlainTextEdit):
    """
    QPlainTextEdit with Up/Down history recall.
    Only triggers when input is empty or caret is at start/end.
    """
    prevRequested = QtCore.pyqtSignal()
    nextRequested = QtCore.pyqtSignal()

    def keyPressEvent(self, e: QtGui.QKeyEvent):
        if e.key() == QtCore.Qt.Key.Key_Up:
            cur = self.textCursor()
            if cur.atStart() or not self.toPlainText().strip():
                self.prevRequested.emit()
                return
        elif e.key() == QtCore.Qt.Key.Key_Down:
            cur = self.textCursor()
            if cur.atEnd() or not self.toPlainText().strip():
                self.nextRequested.emit()
                return
        super().keyPressEvent(e)

class ChatWin(QtWidgets.QWidget):
    sendPrompt = QtCore.pyqtSignal(str)
    modelChanged = QtCore.pyqtSignal(str)

    def __init__(self, prefill: str = ""):
        super().__init__()
        # Rounded floating panel
        self.setWindowFlags(
            QtCore.Qt.WindowType.Tool |
            QtCore.Qt.WindowType.WindowStaysOnTopHint |
            QtCore.Qt.WindowType.FramelessWindowHint
        )
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.resize(620, 420)

        self.settings = QtCore.QSettings(APP_ORG, APP_NAME)
        self._restore_geometry()

        # ---------- Root rounded frame ----------
        self.root = QtWidgets.QFrame(self)
        self.root.setObjectName("RootFrame")
        root_layout = QtWidgets.QVBoxLayout(self.root)
        root_layout.setContentsMargins(12, 12, 12, 12)
        root_layout.setSpacing(10)

        # Outer layout (no margins; we paint rounded with the frame)
        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self.root)

        # ---------- Title bar ----------
        self.modelCombo = QtWidgets.QComboBox(self)
        self.modelCombo.setMinimumWidth(260)
        self.modelCombo.currentTextChanged.connect(self._emit_model_changed)

        self.titleLbl = QtWidgets.QLabel("", self)
        tfont = self.titleLbl.font()
        tfont.setBold(True)
        self.titleLbl.setFont(tfont)

        # Theme toggle
        self.themeBtn = QtWidgets.QToolButton(self)
        self.themeBtn.setToolTip("Toggle theme")
        self.themeBtn.setText("🌙")  # dark icon by default; we flip below
        self.themeBtn.clicked.connect(self._toggle_theme)

        # Close button (since frameless)
        self.closeBtn = QtWidgets.QToolButton(self)
        self.closeBtn.setToolTip("Close (Esc)")
        self.closeBtn.setText("✕")
        self.closeBtn.clicked.connect(self.close)

        # Draggable area (frameless window move)
        self._drag_pos = None

        title_bar = QtWidgets.QHBoxLayout()
        title_bar.setSpacing(8)
        title_bar.addWidget(QtWidgets.QLabel("Model:", self))
        title_bar.addWidget(self.modelCombo, 0)
        title_bar.addStretch(1)
        title_bar.addWidget(self.titleLbl)
        title_bar.addStretch(1)
        title_bar.addWidget(self.themeBtn)
        title_bar.addWidget(self.closeBtn)

        # ---------- Editors + controls ----------
        self.input = HistoryPlainTextEdit(self)
        self.input.setPlaceholderText("Add extra context… (Ctrl+Enter to send)")
        self.input.setPlainText(prefill)
        self.input.prevRequested.connect(self._history_prev)
        self.input.nextRequested.connect(self._history_next)

        self.output = QtWidgets.QTextEdit(self)
        self.output.setReadOnly(True)
        self.output.setPlaceholderText("Model response will appear here…")

        self.sendBtn = QtWidgets.QPushButton("Send", self)
        self.copyBtn = QtWidgets.QPushButton("Copy", self)
        self.clearBtn = QtWidgets.QPushButton("Clear input", self)

        btnrow = QtWidgets.QHBoxLayout()
        btnrow.addWidget(self.sendBtn)
        btnrow.addStretch(1)
        btnrow.addWidget(self.copyBtn)
        btnrow.addWidget(self.clearBtn)

        # Pack into root
        root_layout.addLayout(title_bar)
        root_layout.addWidget(self.input, 1)
        root_layout.addLayout(btnrow)
        root_layout.addWidget(self.output, 2)

        # ---------- History state ----------
        self.history: list[str] = self._load_history()
        self.history_idx: int = len(self.history)  # points after last entry

        # ---------- Signals / Shortcuts ----------
        self.sendBtn.clicked.connect(self._emit_prompt)
        self.copyBtn.clicked.connect(self._copy_response)
        self.clearBtn.clicked.connect(self.clearInput)

        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Enter"), self, activated=self._emit_prompt)
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Return"), self, activated=self._emit_prompt)
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+C"), self, activated=self._copy_response)
        QtGui.QShortcut(QtGui.QKeySequence("Esc"), self, activated=self.close)

        # Hover/focus fade
        self._idle_opacity = 0.88
        self._active_opacity = 1.0
        self.setWindowOpacity(self._active_opacity)
        self.installEventFilter(self)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_Hover, True)

        # Apply theme (persisted)
        theme = self.settings.value(THEME_KEY, "dark")
        self._apply_theme(theme)

    # ---------- Theming ----------
    def _apply_theme(self, theme: str):
        if theme == "dark":
            self.setStyleSheet(DARK_THEME_QSS)
            self.themeBtn.setText("☀️")
            self.settings.setValue(THEME_KEY, "dark")
        else:
            self.setStyleSheet(LIGHT_THEME_QSS)
            self.themeBtn.setText("🌙")
            self.settings.setValue(THEME_KEY, "light")

    def _toggle_theme(self):
        current = self.settings.value(THEME_KEY, "dark")
        self._apply_theme("light" if current == "dark" else "dark")

    # ---------- Public API ----------
    def setModels(self, models: list[str], current: str):
        self.modelCombo.clear()
        self.modelCombo.addItems(models)
        idx = self.modelCombo.findText(current)
        self.modelCombo.setCurrentIndex(idx if idx >= 0 else 0)

    def updateTitleWithModel(self, model: str):
        # Window title (for taskbar) & inline label
        self.setWindowTitle(model)
        self.titleLbl.setText(model)

    def setResponse(self, text: str):
        self.output.setPlainText(text)
        c = self.output.textCursor()
        c.movePosition(QtGui.QTextCursor.MoveOperation.Start)
        self.output.setTextCursor(c)

    def setBusy(self, busy: bool):
        self.sendBtn.setDisabled(busy)
        if busy:
            self.output.setPlainText("Thinking…")

    def clearInput(self):
        self.input.clear()
        self.input.setFocus()
        self.history_idx = len(self.history)

    # ---------- Internals ----------
    def _emit_prompt(self):
        text = self.input.toPlainText().strip()
        if text:
            self._push_history(text)
            self.sendPrompt.emit(text)
            self.clearInput()

    def _copy_response(self):
        txt = self.output.toPlainText().strip()
        if not txt:
            return
        QtWidgets.QApplication.clipboard().setText(txt)
        # toast
        toast = QtWidgets.QLabel("Copied ✓", self.root)
        toast.setStyleSheet("""
            QLabel {
                background: rgba(0,0,0,170);
                color: #ffffff;
                padding: 6px 10px;
                border-radius: 10px;
            }
        """)
        toast.setAttribute(QtCore.Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        toast.adjustSize()
        m = 12
        toast.move(self.root.width() - toast.width() - m, self.root.height() - toast.height() - m)
        toast.show()
        QtCore.QTimer.singleShot(900, toast.close)

    def _emit_model_changed(self, m: str):
        self.modelChanged.emit(m)
        self.updateTitleWithModel(m)

    # ---------- History helpers ----------
    def _load_history(self) -> list[str]:
        v = self.settings.value(HISTORY_KEY, [])
        if isinstance(v, list):
            return [str(x) for x in v][-HISTORY_MAX:]
        if isinstance(v, QtCore.QByteArray):
            try:
                return json.loads(bytes(v).decode("utf-8"))
            except Exception:
                return []
        if isinstance(v, str):
            try:
                data = json.loads(v)
                if isinstance(data, list):
                    return [str(x) for x in data][-HISTORY_MAX:]
            except Exception:
                return []
        return []

    def _save_history(self):
        try:
            self.settings.setValue(HISTORY_KEY, json.dumps(self.history[-HISTORY_MAX:]))
        except Exception:
            pass

    def _push_history(self, text: str):
        text = text.strip()
        if not text:
            return
        if not self.history or self.history[-1] != text:
            self.history.append(text)
            if len(self.history) > HISTORY_MAX:
                self.history = self.history[-HISTORY_MAX:]
            self._save_history()
        self.history_idx = len(self.history)

    def _history_prev(self):
        if not self.history:
            return
        if self.history_idx > 0:
            self.history_idx -= 1
            self._set_input_from_history()

    def _history_next(self):
        if not self.history:
            return
        if self.history_idx < len(self.history) - 1:
            self.history_idx += 1
            self._set_input_from_history()
        else:
            self.history_idx = len(self.history)
            self.input.clear()

    def _set_input_from_history(self):
        if 0 <= self.history_idx < len(self.history):
            self.input.setPlainText(self.history[self.history_idx])
            c = self.input.textCursor()
            c.movePosition(QtGui.QTextCursor.MoveOperation.End)
            self.input.setTextCursor(c)
            self.input.setFocus()

    # ---------- Frameless window drag ----------
    def mousePressEvent(self, e: QtGui.QMouseEvent):
        if e.button() == QtCore.Qt.MouseButton.LeftButton:
            self._drag_pos = e.globalPosition().toPoint() - self.frameGeometry().topLeft()
            e.accept()

    def mouseMoveEvent(self, e: QtGui.QMouseEvent):
        if self._drag_pos and e.buttons() & QtCore.Qt.MouseButton.LeftButton:
            self.move(e.globalPosition().toPoint() - self._drag_pos)
            e.accept()

    def mouseReleaseEvent(self, e: QtGui.QMouseEvent):
        self._drag_pos = None
        super().mouseReleaseEvent(e)

    # ---------- Fade on focus ----------
    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.Type.WindowDeactivate:
            self._fade_to(self._idle_opacity)
        elif event.type() in (QtCore.QEvent.Type.WindowActivate,
                              QtCore.QEvent.Type.HoverEnter,
                              QtCore.QEvent.Type.Enter):
            self._fade_to(self._active_opacity)
        elif event.type() in (QtCore.QEvent.Type.HoverLeave,
                              QtCore.QEvent.Type.Leave):
            if not self.isActiveWindow():
                self._fade_to(self._idle_opacity)
        return super().eventFilter(obj, event)

    def _fade_to(self, target: float, duration_ms: int = 140):
        anim = QtCore.QPropertyAnimation(self, b"windowOpacity", self)
        anim.setDuration(duration_ms)
        anim.setStartValue(self.windowOpacity())
        anim.setEndValue(target)
        anim.setEasingCurve(QtCore.QEasingCurve.Type.InOutQuad)
        anim.finished.connect(anim.deleteLater)
        anim.start(QtCore.QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

    # ---------- Persist geometry ----------
    def closeEvent(self, e: QtGui.QCloseEvent):
        self._save_geometry()
        return super().closeEvent(e)

    def _save_geometry(self):
        self.settings.setValue("geometry", self.saveGeometry())

    def _restore_geometry(self):
        g = self.settings.value("geometry")
        if isinstance(g, QtCore.QByteArray) and not g.isEmpty():
            self.restoreGeometry(g)

# ---------- Factory ----------
def open_chat(prefill: str, on_send):
    """
    Create, connect, and SHOW the ChatWin. Return the widget to the caller.
    """
    app = QtWidgets.QApplication.instance()
    if app is None:
        raise RuntimeError("QApplication must exist before calling open_chat().")
    w = ChatWin(prefill)
    w.sendPrompt.connect(lambda t: on_send(w, t))
    w.show()
    return w
