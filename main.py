import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QGroupBox, QHeaderView,
    QAbstractItemView, QMessageBox, QDialog
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from db import AccountDB, DISPLAY_FIELDS, READONLY_FIELDS
from dialogs import AddAccountDialog, BatchEditDialog, clean_input_text
from actions import login, start
from config import UI_CONFIG, FIELDS_TO_CLEAN, APP_CONFIG


class AccountManager(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(UI_CONFIG["window_title"])
        self.resize(*UI_CONFIG["window_size"])
        self.db = AccountDB()
        self.row_ids = []
        self._font = QFont(UI_CONFIG["font_family"], UI_CONFIG["font_size"])
        self.init_ui()
        self.load_from_db()
        
        if APP_CONFIG.get("show_help_on_start", False):
            self.show_help()

    def init_ui(self):
        main_layout = QVBoxLayout()

        # 顶部按钮组
        top_group = QGroupBox()
        top_layout = QHBoxLayout()
        
        add_btn = QPushButton("添加账号")
        add_btn.clicked.connect(self.on_add)
        
        select_all_btn = QPushButton("全选/取消全选")
        select_all_btn.clicked.connect(self.on_toggle_select_all)
        
        delete_btn = QPushButton("删除选中")
        delete_btn.clicked.connect(self.on_delete_selected)
        
        batch_btn = QPushButton("批量编辑")
        batch_btn.clicked.connect(self.on_batch_edit)
        
        help_btn = QPushButton("?")
        help_btn.clicked.connect(self.show_help)
        
        top_layout.addWidget(add_btn)
        top_layout.addWidget(select_all_btn)
        top_layout.addWidget(delete_btn)
        top_layout.addWidget(batch_btn)
        top_layout.addStretch()
        top_layout.addWidget(help_btn)
        
        top_group.setLayout(top_layout)
        main_layout.addWidget(top_group)

        # 表格设置
        self.table = QTableWidget(0, len(DISPLAY_FIELDS) + 2)
        headers = ["选中"] + DISPLAY_FIELDS + ["功能"]
        self.table.setHorizontalHeaderLabels(headers)
        self.table.verticalHeader().setVisible(False)
        self.table.setFont(self._font)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.DoubleClicked | 
            QAbstractItemView.EditTrigger.SelectedClicked
        )
        
        main_layout.addWidget(self.table)
        self.setLayout(main_layout)

        self.table.itemChanged.connect(self.on_item_changed)

    def load_from_db(self):
        """从数据库加载数据"""
        all_data = self.db.load_all()
        for data in all_data:
            self._add_row(data, save_db=False)
        self.row_ids = self.db.get_ids()

    def _add_row(self, values, save_db=True):
        """添加表格行"""
        row = self.table.rowCount()
        self.table.insertRow(row)

        # 添加复选框
        chk_item = QTableWidgetItem()
        chk_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
        chk_item.setCheckState(Qt.CheckState.Unchecked)
        self.table.setItem(row, 0, chk_item)

        # 添加数据字段
        for col, val in enumerate(values, start=1):
            item = QTableWidgetItem(str(val))
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            field_name = DISPLAY_FIELDS[col - 1]
            if field_name in READONLY_FIELDS:
                item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            else:
                item.setFlags(
                    Qt.ItemFlag.ItemIsSelectable | 
                    Qt.ItemFlag.ItemIsEditable | 
                    Qt.ItemFlag.ItemIsEnabled
                )
            
            self.table.setItem(row, col, item)

        # 添加功能按钮
        self._add_action_buttons(row)

        if save_db:
            self.db.add(values)
            self.row_ids = self.db.get_ids()

    def _add_action_buttons(self, row):
        """添加功能按钮"""
        from PyQt6.QtWidgets import QWidget, QHBoxLayout
        
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        login_btn = QPushButton("登录")
        login_btn.clicked.connect(lambda _, r=row: self.safe_login(r))
        
        start_btn = QPushButton("开始")
        start_btn.clicked.connect(lambda _, r=row: self.safe_start(r))
        
        del_btn = QPushButton("删除")
        del_btn.clicked.connect(lambda _, r=row: self.on_delete_row(r))

        for btn in [login_btn, start_btn, del_btn]:
            layout.addWidget(btn)

        self.table.setCellWidget(row, len(DISPLAY_FIELDS) + 1, container)

    def safe_login(self, row):
        """安全登录调用"""
        if row >= len(self.row_ids):
            return
        login(row, self.table, self.db, self.row_ids)

    def safe_start(self, row):
        """安全开始调用"""
        if row >= len(self.row_ids):
            return
        start(row, self.table, self.db, self.row_ids)

    def on_item_changed(self, item):
        """表格项目更改事件"""
        row = item.row()
        col = item.column()
        
        if row >= len(self.row_ids) or col == 0:  # 跳过复选框列
            return
        
        field_index = col - 1
        if field_index < len(DISPLAY_FIELDS):
            field_name = DISPLAY_FIELDS[field_index]
            current_text = item.text()
            
            if field_name in FIELDS_TO_CLEAN:
                cleaned_text = clean_input_text(current_text)
                if cleaned_text != current_text:
                    item.setText(cleaned_text)
                    return  # 避免递归调用
        
        # 保存到数据库
        row_id = self.row_ids[row]
        values = []
        for c in range(1, len(DISPLAY_FIELDS) + 1):
            table_item = self.table.item(row, c)
            text = table_item.text() if table_item else ""
            
            # 对需要清理的字段进行处理
            field_name = DISPLAY_FIELDS[c - 1]
            if field_name in FIELDS_TO_CLEAN:
                text = clean_input_text(text)
            else:
                text = text.strip()
            
            values.append(text)
        
        if APP_CONFIG.get("auto_save", True):
            self.db.update(row_id, values)

    def on_add(self):
        """添加账号"""
        dialog = AddAccountDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._add_row(dialog.get_data())

    def on_toggle_select_all(self):
        """切换全选状态"""
        if self.table.rowCount() == 0:
            return
            
        all_checked = all(
            self.table.item(r, 0).checkState() == Qt.CheckState.Checked 
            for r in range(self.table.rowCount())
        )
        
        new_state = Qt.CheckState.Unchecked if all_checked else Qt.CheckState.Checked
        
        for r in range(self.table.rowCount()):
            self.table.item(r, 0).setCheckState(new_state)

    def get_checked_rows(self):
        """获取选中的行"""
        return [
            r for r in range(self.table.rowCount()) 
            if self.table.item(r, 0).checkState() == Qt.CheckState.Checked
        ]

    def on_delete_selected(self):
        """删除选中的行"""
        rows = self.get_checked_rows()
        if not rows:
            QMessageBox.warning(self, "提示", "请先选择要删除的行")
            return
        
        if APP_CONFIG.get("confirm_delete", True):
            reply = QMessageBox.question(
                self, "确认删除", 
                f"确定要删除选中的 {len(rows)} 个账号吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        
        # 从后往前删除，避免索引问题
        for r in sorted(rows, reverse=True):
            self.on_delete_row(r)

    def on_delete_row(self, row):
        """删除指定行"""
        if row < len(self.row_ids):
            self.db.delete(self.row_ids[row])
            del self.row_ids[row]
        self.table.removeRow(row)

    def on_batch_edit(self):
        """批量编辑"""
        rows = self.get_checked_rows()
        if not rows:
            QMessageBox.warning(self, "提示", "请先勾选要修改的行")
            return
        
        dialog = BatchEditDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            changes = dialog.get_changes()
            if not changes:
                return
            
            for r in rows:
                if r >= len(self.row_ids):
                    continue
                
                row_id = self.row_ids[r]
                
                # 更新表格显示
                for c, field in enumerate(DISPLAY_FIELDS, start=1):
                    if field in changes:
                        self.table.item(r, c).setText(changes[field])
                
                # 获取完整的行数据并保存
                values = []
                for c in range(1, len(DISPLAY_FIELDS) + 1):
                    table_item = self.table.item(r, c)
                    values.append(table_item.text() if table_item else "")
                
                self.db.update(row_id, values)

    def show_help(self):
        """显示帮助信息"""
        help_text = (
            "📘 账号管理器使用教程：\n\n"
            "🔹 添加账号：账号和密码必填，其他字段可留空\n"
            "🔹 自动清理：账号、密码、2FA字段会自动去除空格\n"
            "🔹 双击编辑：可编辑备注、账号、密码、2FA、代理字段\n"
            "🔹 只读字段：状态、粉丝、点赞、Cookie为系统维护\n"
            "🔹 批量操作：勾选左侧复选框进行批量删除或编辑\n"
            "🔹 功能按钮：登录测试账号，开始执行任务，删除单行\n\n"
            "💡 提示：所有修改会自动保存到数据库"
        )
        QMessageBox.information(self, "使用帮助", help_text)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AccountManager()
    window.show()
    sys.exit(app.exec())
