# actions.py
import json
import sys
import os
from PyQt6.QtWidgets import QMessageBox
from db import EDITABLE_FIELDS, READONLY_FIELDS, DISPLAY_FIELDS
from dialogs import clean_input_text
from config import FIELDS_TO_CLEAN

# 添加当前目录到 Python 路径，以便导入 inslogin 模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入登录模块
try:
    from inslogin import login as instagram_login
except ImportError:
    print("警告: 无法导入 inslogin 模块，登录功能将不可用")
    instagram_login = None


def get_account_data(row, table):
    """获取账号数据并清理输入"""
    data = {}
    for i, field in enumerate(DISPLAY_FIELDS):
        item = table.item(row, i + 1)
        text = item.text() if item else ""
        
        if field in FIELDS_TO_CLEAN:
            text = clean_input_text(text)
        else:
            text = text.strip()
            
        data[field] = text
    
    return data


def login(row, table, db, row_ids):
    """登录功能 - 使用 inslogin.py 进行实际登录"""
    try:
        # 检查登录模块是否可用
        if instagram_login is None:
            QMessageBox.warning(table, "登录失败", "登录模块不可用，请检查 inslogin.py 文件")
            return False
        
        account_data = get_account_data(row, table)
        
        account = account_data["账号"]
        password = account_data["密码"]
        two_fa = account_data["2FA"]
        proxy = account_data["代理"]
        
        # 验证必要字段
        if not account or not password:
            QMessageBox.warning(table, "登录失败", "账号和密码不能为空！")
            return False
        
        # 调用 inslogin.py 的登录函数
        login_result = instagram_login(account, password, two_fa, proxy)
        
        # 处理登录结果
        if login_result["status"] == "登录成功":
            # 更新状态和Cookie
            status_col = DISPLAY_FIELDS.index("状态") + 1
            cookie_col = DISPLAY_FIELDS.index("Cookie") + 1
            
            # 格式化 Cookie 为 JSON 字符串
            cookie_json = json.dumps(login_result["cookies"], ensure_ascii=False)
            
            table.item(row, status_col).setText("在线")
            table.item(row, cookie_col).setText(cookie_json)
            
            # 保存到数据库
            if row < len(row_ids):
                row_id = row_ids[row]
                values = [table.item(row, c).text() for c in range(1, len(DISPLAY_FIELDS) + 1)]
                db.update(row_id, values)
            
            print(f"✅ 账号 '{account}' 登录成功")
            QMessageBox.information(table, "登录成功", f"账号 '{account}' 登录成功！")
            return True
        else:
            # 登录失败，显示错误信息
            error_msg = login_result["status"]
            print(f"❌ 账号 '{account}' 登录失败: {error_msg}")
            
            # 更新状态为离线
            status_col = DISPLAY_FIELDS.index("状态") + 1
            table.item(row, status_col).setText("离线")
            
            # 保存到数据库
            if row < len(row_ids):
                row_id = row_ids[row]
                values = [table.item(row, c).text() for c in range(1, len(DISPLAY_FIELDS) + 1)]
                db.update(row_id, values)
            
            QMessageBox.warning(table, "登录失败", f"账号 '{account}' 登录失败: {error_msg}")
            return False
        
    except Exception as e:
        print(f"❌ 登录过程中发生错误: {str(e)}")
        QMessageBox.critical(table, "登录错误", f"登录过程中发生错误：{str(e)}")
        return False


def start(row, table, db, row_ids):
    """开始执行功能 - 测试阶段"""
    try:
        # 检查登录状态
        status_col = DISPLAY_FIELDS.index("状态") + 1
        current_status = table.item(row, status_col).text()
        
        if current_status != "在线":
            QMessageBox.warning(table, "操作失败", "请先登录账号再执行任务！")
            return False
        
        account_data = get_account_data(row, table)
        account = account_data["账号"]
        
        print(f"🚀 开始执行任务 - 账号: '{account}'")
        
        # 更新状态为执行中
        table.item(row, status_col).setText("执行中...")
        
        # 模拟任务执行（测试阶段）
        import time
        print(f"⏳ 账号 '{account}' 正在执行任务...")
        
        # 这里可以添加实际的任务逻辑
        # time.sleep(2)  # 模拟任务执行时间
        
        # 保存状态到数据库
        if row < len(row_ids):
            row_id = row_ids[row]
            values = [table.item(row, c).text() for c in range(1, len(DISPLAY_FIELDS) + 1)]
            db.update(row_id, values)
        
        print(f"✅ 账号 '{account}' 任务启动成功")
        return True
        
    except Exception as e:
        print(f"❌ 执行任务时发生错误: {str(e)}")
        QMessageBox.critical(table, "执行错误", f"执行任务时发生错误：{str(e)}")
        
        # 恢复状态
        status_col = DISPLAY_FIELDS.index("状态") + 1
        table.item(row, status_col).setText("在线")
        return False


def update_account_stats(row, table, db, row_ids, fans_count=None, likes_count=None):
    """更新账号统计信息"""
    try:
        if fans_count is not None:
            fans_col = DISPLAY_FIELDS.index("粉丝") + 1
            table.item(row, fans_col).setText(str(fans_count))
        
        if likes_count is not None:
            likes_col = DISPLAY_FIELDS.index("点赞") + 1
            table.item(row, likes_col).setText(str(likes_count))
        
        # 保存到数据库
        if row < len(row_ids):
            row_id = row_ids[row]
            values = [table.item(row, c).text() for c in range(1, len(DISPLAY_FIELDS) + 1)]
            db.update(row_id, values)
        
        return True
        
    except Exception as e:
        print(f"❌ 更新统计信息时发生错误: {str(e)}")
        return False