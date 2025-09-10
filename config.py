# config.py - 项目配置文件

# 数据库配置
DB_CONFIG = {
    "db_file": "accounts.db",  # 数据库文件名
    "table_name": "accounts"   # 数据表名
}

# 界面配置
UI_CONFIG = {
    "window_title": "账号管理器",  # 窗口标题
    "window_size": (1200, 600),   # 窗口大小 (宽, 高)
    "font_family": "微软雅黑",     # 字体
    "font_size": 10               # 字体大小
}

# 需要自动清理空格的字段
FIELDS_TO_CLEAN = ["账号", "密码", "2FA"]

# 输入验证配置
VALIDATION_CONFIG = {
    "required_fields": ["账号", "密码"],  # 必填字段
    "max_length": {                      # 字段最大长度限制
        "备注": 100,
        "账号": 50,
        "密码": 50,
        "2FA": 20,
        "代理": 100
    }
}

# 应用设置
APP_CONFIG = {
    "auto_save": True,           # 自动保存
    "confirm_delete": True,      # 删除确认
    "show_help_on_start": False  # 启动时显示帮助
}
