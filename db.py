# db.py
import sqlite3
import logging
from config import DB_CONFIG

# 定义程序中使用的所有字段常量
# 可编辑字段
EDITABLE_FIELDS = ["备注", "账号", "密码", "2FA", "代理"]
# 只读字段
READONLY_FIELDS = ["状态", "粉丝", "点赞", "Cookie"]
# 表格中显示的完整字段列表（顺序很重要）
DISPLAY_FIELDS = ["备注", "账号", "密码", "2FA", "代理", "状态", "粉丝", "点赞", "Cookie"]


logger = logging.getLogger(__name__)


class AccountDB:
    """数据库操作类"""

    def __init__(self):
        self.db_file = DB_CONFIG["db_file"]
        self.table_name = DB_CONFIG["table_name"]
        self.conn = sqlite3.connect(self.db_file)
        self.cursor = self.conn.cursor()
        self.create_table()

    # --- 上下文管理 -----------------------------------------------------

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()

    def close(self):
        if getattr(self, "conn", None):
            self.conn.close()
            self.conn = None
            self.cursor = None

    def create_table(self):
        """创建数据表"""
        # 使用带引号的字段名以支持中文字段
        columns = [f'"{field}" TEXT' for field in DISPLAY_FIELDS]
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS "{self.table_name}" (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            {', '.join(columns)}
        );
        """
        self.cursor.execute(create_table_sql)
        self.conn.commit()

    def load_all(self):
        """加载所有账号数据"""
        quoted_fields = ', '.join([f'"{f}"' for f in DISPLAY_FIELDS])
        try:
            self.cursor.execute(
                f'SELECT {quoted_fields} FROM "{self.table_name}" ORDER BY id'
            )
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            logger.error("加载数据失败: %s", e)
            raise

    def add(self, values):
        """添加一条账号数据"""
        placeholders = ', '.join(['?' for _ in DISPLAY_FIELDS])
        quoted_fields = ', '.join([f'"{f}"' for f in DISPLAY_FIELDS])
        sql = f'INSERT INTO "{self.table_name}" ({quoted_fields}) VALUES ({placeholders})'
        try:
            self.cursor.execute(sql, values)
            self.conn.commit()
        except sqlite3.Error as e:
            logger.error("添加数据失败: %s", e)
            raise

    def update(self, row_id, values):
        """根据数据库ID更新一条数据"""
        set_clause = ', '.join([f'"{field}" = ?' for field in DISPLAY_FIELDS])
        sql = f'UPDATE "{self.table_name}" SET {set_clause} WHERE id = ?'
        try:
            self.cursor.execute(sql, values + [row_id])
            if self.cursor.rowcount == 0:
                raise ValueError(f"ID {row_id} 不存在")
            self.conn.commit()
        except sqlite3.Error as e:
            logger.error("更新数据失败: %s", e)
            raise

    def delete(self, row_id):
        """根据数据库ID删除一条数据"""
        sql = f'DELETE FROM "{self.table_name}" WHERE id = ?'
        try:
            self.cursor.execute(sql, (row_id,))
            if self.cursor.rowcount == 0:
                raise ValueError(f"ID {row_id} 不存在")
            self.conn.commit()
        except sqlite3.Error as e:
            logger.error("删除数据失败: %s", e)
            raise

    def get_ids(self):
        """获取所有数据的数据库ID列表"""
        self.cursor.execute(f'SELECT id FROM "{self.table_name}" ORDER BY id')
        return [item[0] for item in self.cursor.fetchall()]

    def __del__(self):
        """确保对象被销毁时连接被关闭"""
        self.close()
