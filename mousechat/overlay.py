# mousechat/overlay.py
from PyQt6 import QtCore, QtGui, QtWidgets

class AskChip(QtWidgets.QPushButton):
    def __init__(self, text="Ask ChatGPT", parent=None):
        super().__init__(text, parent)
        self.setWindowFlags(
            QtCore.Qt.WindowType.FramelessWindowHint |
            QtCore.Qt.WindowType.Tool |
            QtCore.Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("""
            QPushButton {
                border: 1px solid rgba(0,0,0,60);
                background: rgba(255,255,255,230);
                border-radius: 12px;
                padding: 6px 10px;
                font-size: 12px;
            }
            QPushButton:hover { background: rgba(245,245,245,240); }
        """)

def show_chip_near_cursor(callback):
    app = QtWidgets.QApplication.instance()
    if app is None:
        raise RuntimeError("QApplication must exist before show_chip_near_cursor().")

    chip = AskChip()
    chip.clicked.connect(lambda: (chip.close(), callback()))

    pos = QtGui.QCursor.pos()
    chip.move(pos.x() + 12, pos.y() + 12)
    chip.show()

    # Auto-hide if ignored
    QtCore.QTimer.singleShot(2500, chip.close)

    # Ensure it paints
    app.processEvents()
