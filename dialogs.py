from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QLabel, QDialogButtonBox,
    QVBoxLayout, QHBoxLayout, QWidget, QCheckBox, QMessageBox
)
from db import EDITABLE_FIELDS
from config import FIELDS_TO_CLEAN, VALIDATION_CONFIG


def clean_input_text(text: str) -> str:
    """清理输入文本：去除所有空格和前后空白字符"""
    return text.replace(" ", "").replace("\t", "").replace("\n", "").strip()


def auto_clean_input(line_edit: QLineEdit, field_name: str):
    """自动清理特定字段的输入"""
    if field_name in FIELDS_TO_CLEAN:
        current_text = line_edit.text()
        cleaned_text = clean_input_text(current_text)
        
        if cleaned_text != current_text:
            # 保存光标位置
            cursor_pos = line_edit.cursorPosition()
            # 设置清理后的文本
            line_edit.setText(cleaned_text)
            # 调整光标位置
            new_cursor_pos = min(cursor_pos, len(cleaned_text))
            line_edit.setCursorPosition(new_cursor_pos)


class AddAccountDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("添加账号")
        self.inputs = {}
        form = QFormLayout()
        
        for field in EDITABLE_FIELDS:
            line_edit = QLineEdit()
            
            # 设置占位符文本
            if field in VALIDATION_CONFIG["required_fields"]:
                line_edit.setPlaceholderText("必填")
            else:
                line_edit.setPlaceholderText("可留空")
            
            # 设置最大长度
            if field in VALIDATION_CONFIG["max_length"]:
                line_edit.setMaxLength(VALIDATION_CONFIG["max_length"][field])
            
            line_edit.textChanged.connect(
                lambda _, le=line_edit, f=field: auto_clean_input(le, f)
            )
            
            form.addRow(QLabel(field + ":"), line_edit)
            self.inputs[field] = line_edit

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.validate)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def validate(self):
        """验证输入数据"""
        errors = []
        
        for field in VALIDATION_CONFIG["required_fields"]:
            text = clean_input_text(self.inputs[field].text())
            if not text:
                errors.append(f"{field}为必填项")
        
        if errors:
            QMessageBox.warning(self, "输入错误", "\n".join(errors))
            return
        
        # 最终清理所有输入
        for field, line_edit in self.inputs.items():
            if field in FIELDS_TO_CLEAN:
                cleaned_text = clean_input_text(line_edit.text())
                line_edit.setText(cleaned_text)
            else:
                # 其他字段只去除前后空白
                line_edit.setText(line_edit.text().strip())
        
        self.accept()

    def get_data(self):
        """获取表单数据"""
        values = []
        for field in EDITABLE_FIELDS:
            text = self.inputs[field].text()
            if field in FIELDS_TO_CLEAN:
                text = clean_input_text(text)
            else:
                text = text.strip()
            values.append(text)
        
        # 添加默认的只读字段值
        values += ["离线", "0", "0", ""]  # 状态, 粉丝, 点赞, Cookie
        return values


class BatchEditDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("批量编辑")
        self.checks = {}
        self.inputs = {}

        layout = QFormLayout()
        
        for field in EDITABLE_FIELDS:
            hbox = QHBoxLayout()
            
            checkbox = QCheckBox()
            line_edit = QLineEdit()
            line_edit.setEnabled(False)
            
            # 设置最大长度
            if field in VALIDATION_CONFIG["max_length"]:
                line_edit.setMaxLength(VALIDATION_CONFIG["max_length"][field])
            
            line_edit.textChanged.connect(
                lambda _, le=line_edit, f=field: auto_clean_input(le, f)
            )
            
            checkbox.toggled.connect(line_edit.setEnabled)
            
            hbox.addWidget(checkbox)
            hbox.addWidget(line_edit)
            
            row_widget = QWidget()
            row_widget.setLayout(hbox)
            
            layout.addRow(QLabel(field + ":"), row_widget)
            
            self.checks[field] = checkbox
            self.inputs[field] = line_edit

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)

        main_layout = QVBoxLayout()
        main_layout.addWidget(
            QLabel("说明：勾选并输入值 → 应用到所有选中行。\n只支持修改备注、账号、密码、2FA、代理。")
        )
        main_layout.addLayout(layout)
        main_layout.addWidget(buttons)
        self.setLayout(main_layout)

    def validate_and_accept(self):
        """验证并接受批量编辑"""
        has_changes = any(self.checks[field].isChecked() for field in EDITABLE_FIELDS)
        
        if not has_changes:
            QMessageBox.warning(self, "提示", "请至少选择一个字段进行修改")
            return
        
        # 最终清理选中字段的输入
        for field in EDITABLE_FIELDS:
            if self.checks[field].isChecked():
                line_edit = self.inputs[field]
                if field in FIELDS_TO_CLEAN:
                    cleaned_text = clean_input_text(line_edit.text())
                    line_edit.setText(cleaned_text)
                else:
                    line_edit.setText(line_edit.text().strip())
        
        self.accept()

    def get_changes(self):
        """获取要应用的更改"""
        changes = {}
        for field in EDITABLE_FIELDS:
            if self.checks[field].isChecked():
                text = self.inputs[field].text()
                if field in FIELDS_TO_CLEAN:
                    text = clean_input_text(text)
                else:
                    text = text.strip()
                changes[field] = text
        return changes
