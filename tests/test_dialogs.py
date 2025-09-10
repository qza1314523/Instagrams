import sys
import types

def import_clean_input_text(monkeypatch):
    """导入 dialogs.clean_input_text，并在未安装 PyQt6 的环境下工作"""
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

    from dialogs import clean_input_text

    return clean_input_text


def test_clean_input_text(monkeypatch):
    clean_input_text = import_clean_input_text(monkeypatch)
    assert clean_input_text(" a b\tc\n") == "abc"
    assert clean_input_text("abc") == "abc"
