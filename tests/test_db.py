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
    """使用内存数据库并通过上下文管理器确保连接关闭"""
    monkeypatch.setitem(db_module.DB_CONFIG, "db_file", ":memory:")
    with db_module.AccountDB() as db:
        yield db


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


def test_update_missing_row(account_db):
    with pytest.raises(ValueError):
        account_db.update(999, SAMPLE_VALUES1)


def test_delete_missing_row(account_db):
    with pytest.raises(ValueError):
        account_db.delete(999)
