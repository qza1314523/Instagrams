import sys
import types
from collections import defaultdict


def import_update_account_stats(monkeypatch):
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

    from actions import update_account_stats, DISPLAY_FIELDS

    return update_account_stats, DISPLAY_FIELDS


class Item:
    def __init__(self, text=""):
        self._text = text

    def text(self):
        return self._text

    def setText(self, text):
        self._text = text


class TableStub:
    def __init__(self, rows, cols):
        self._items = defaultdict(dict)
        for r in range(rows):
            for c in range(cols):
                self._items[r][c] = Item()

    def item(self, row, col):
        return self._items.get(row, {}).get(col)


class DummyDB:
    def __init__(self):
        self.updated = []

    def update(self, row_id, values):
        self.updated.append((row_id, values))


def test_update_account_stats_success(monkeypatch):
    update_account_stats, DISPLAY_FIELDS = import_update_account_stats(monkeypatch)
    table = TableStub(1, len(DISPLAY_FIELDS) + 1)
    db = DummyDB()
    row_ids = [1]

    assert update_account_stats(0, table, db, row_ids, fans_count=10, likes_count=5)
    fans_col = DISPLAY_FIELDS.index("粉丝") + 1
    likes_col = DISPLAY_FIELDS.index("点赞") + 1
    assert table.item(0, fans_col).text() == "10"
    assert table.item(0, likes_col).text() == "5"
    assert db.updated


def test_update_account_stats_missing_cell(monkeypatch):
    update_account_stats, DISPLAY_FIELDS = import_update_account_stats(monkeypatch)
    table = TableStub(1, len(DISPLAY_FIELDS) + 1)
    fans_col = DISPLAY_FIELDS.index("粉丝") + 1
    table._items[0][fans_col] = None  # 模拟缺失单元格
    db = DummyDB()
    row_ids = [1]

    assert not update_account_stats(0, table, db, row_ids, fans_count=10)
