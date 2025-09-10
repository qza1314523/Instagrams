import sys
import types


def import_dialog_utils(monkeypatch):
    """导入 dialogs 中的工具函数，并在未安装 PyQt6 的环境下工作"""
    qtwidgets = types.ModuleType("PyQt6.QtWidgets")
    for name in [
        "QDialog",
        "QFormLayout",
        "QLineEdit",
        "QLabel",
        "QDialogButtonBox",
        "QVBoxLayout",
        "QHBoxLayout",
        "QWidget",
        "QCheckBox",
        "QMessageBox",
    ]:
        setattr(qtwidgets, name, type(name, (), {}))

    pyqt6 = types.ModuleType("PyQt6")
    monkeypatch.setitem(sys.modules, "PyQt6", pyqt6)
    monkeypatch.setitem(sys.modules, "PyQt6.QtWidgets", qtwidgets)

    from dialogs import clean_input_text, auto_clean_input

    return clean_input_text, auto_clean_input


def test_clean_input_text(monkeypatch):
    clean_input_text, _ = import_dialog_utils(monkeypatch)
    assert clean_input_text(" a b\tc\n\r　") == "abc"
    assert clean_input_text("abc") == "abc"


def test_auto_clean_input(monkeypatch):
    _, auto_clean_input = import_dialog_utils(monkeypatch)

    class StubLineEdit:
        def __init__(self, text, cursor):
            self._text = text
            self._cursor = cursor

        def text(self):
            return self._text

        def setText(self, text):
            self._text = text

        def cursorPosition(self):
            return self._cursor

        def setCursorPosition(self, pos):
            self._cursor = pos

    le = StubLineEdit(" a b", 3)
    auto_clean_input(le, "账号")
    assert le.text() == "ab"
    assert le.cursorPosition() == 2

    le2 = StubLineEdit("abc", 1)
    auto_clean_input(le2, "账号")
    assert le2.text() == "abc"
    assert le2.cursorPosition() == 1
