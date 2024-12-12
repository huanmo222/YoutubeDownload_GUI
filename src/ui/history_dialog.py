from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHBoxLayout, QHeaderView, QMessageBox
)
from PyQt6.QtCore import Qt
from utils.history import DownloadHistory, DownloadRecord
from typing import Callable

class HistoryDialog(QDialog):
    def __init__(self, redownload_callback: Callable[[str, str], None], parent=None):
        super().__init__(parent)
        self.history = DownloadHistory()
        self.redownload_callback = redownload_callback
        self.init_ui()
        self.load_history()
        
    def init_ui(self):
        self.setWindowTitle("下载历史")
        self.setGeometry(200, 200, 800, 400)
        
        layout = QVBoxLayout(self)
        
        # 创建表格
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels([
            "文件名", "URL", "保存路径", "开始时间", "状态", "操作"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self.table)
        
        # 添加底部按钮
        btn_layout = QHBoxLayout()
        clear_btn = QPushButton("清空历史")
        refresh_btn = QPushButton("刷新")
        close_btn = QPushButton("关闭")
        
        clear_btn.clicked.connect(self.clear_history)
        refresh_btn.clicked.connect(self.load_history)
        close_btn.clicked.connect(self.accept)
        
        btn_layout.addWidget(clear_btn)
        btn_layout.addWidget(refresh_btn)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
        
    def load_history(self):
        """加载历史记录"""
        records = self.history.get_records()
        self.table.setRowCount(len(records))
        
        for row, record in enumerate(records):
            self.table.setItem(row, 0, QTableWidgetItem(record.filename))
            self.table.setItem(row, 1, QTableWidgetItem(record.url))
            self.table.setItem(row, 2, QTableWidgetItem(record.save_path))
            self.table.setItem(row, 3, QTableWidgetItem(
                record.start_time.strftime("%Y-%m-%d %H:%M:%S")
            ))
            self.table.setItem(row, 4, QTableWidgetItem(record.status))
            
            # 添加重新下载按钮
            redownload_btn = QPushButton("重新下载")
            redownload_btn.clicked.connect(
                lambda checked, r=record: self.redownload_callback(r.url, r.save_path)
            )
            self.table.setCellWidget(row, 5, redownload_btn)
            
    def clear_history(self):
        """清空历史记录"""
        if QMessageBox.question(
            self,
            "确认",
            "确定要清空所有下载历史记录吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            self.history.clear_all()
            self.table.setRowCount(0)