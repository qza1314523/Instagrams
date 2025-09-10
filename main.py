from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QHBoxLayout,
)


class AccountTable(QTableWidget):
    """Simple table for managing Instagram accounts."""

    HEADERS = [
        "序号",
        "账号",
        "密码",
        "2FA",
        "备注",
        "代理",
        "抓取",
        "关注",
        "点赞",
        "状态",
        "功能",
    ]

    def __init__(self) -> None:
        super().__init__(0, len(self.HEADERS))
        self.setHorizontalHeaderLabels(self.HEADERS)

    def add_empty_row(self) -> None:
        """Add an empty row with action buttons."""
        row = self.rowCount()
        self.insertRow(row)
        self.setItem(row, 0, QTableWidgetItem(str(row + 1)))
        for col in range(1, 10):
            self.setItem(row, col, QTableWidgetItem(""))

        init_btn = QPushButton("初始化")
        start_btn = QPushButton("开始")
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(init_btn)
        layout.addWidget(start_btn)
        self.setCellWidget(row, 10, container)


def main() -> None:
    app = QApplication([])
    table = AccountTable()
    table.add_empty_row()
    table.resize(1000, 300)
    table.show()
    app.exec()


if __name__ == "__main__":
    main()
