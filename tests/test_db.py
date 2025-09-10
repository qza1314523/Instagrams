import pytest
import db as db_module

SAMPLE_VALUES1 = [
    "备注1",
    "账号1",
    "密码1",
    "2FA1",
    "代理1",
    "状态1",
    "100",
    "10",
    "cookie1",
]

SAMPLE_VALUES2 = [
    "备注2",
    "账号2",
    "密码2",
    "2FA2",
    "代理2",
    "状态2",
    "200",
    "20",
    "cookie2",
]


@pytest.fixture
def account_db(monkeypatch):
    # 使用内存数据库以避免对真实文件的影响
    monkeypatch.setitem(db_module.DB_CONFIG, "db_file", ":memory:")
    db = db_module.AccountDB()
    yield db
    del db  # 确保连接关闭


def test_add_and_load(account_db):
    account_db.add(SAMPLE_VALUES1)
    rows = account_db.load_all()
    assert rows == [tuple(SAMPLE_VALUES1)]


def test_update(account_db):
    account_db.add(SAMPLE_VALUES1)
    row_id = account_db.get_ids()[0]
    account_db.update(row_id, SAMPLE_VALUES2)
    rows = account_db.load_all()
    assert rows == [tuple(SAMPLE_VALUES2)]


def test_delete(account_db):
    account_db.add(SAMPLE_VALUES1)
    row_id = account_db.get_ids()[0]
    account_db.delete(row_id)
    assert account_db.load_all() == []
