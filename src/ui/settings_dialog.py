from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QCheckBox, QPushButton, QFileDialog,
    QComboBox, QGroupBox, QSpinBox
)
from utils.config import AppConfig

class SettingsDialog(QDialog):
    def __init__(self, config: AppConfig, parent=None):
        super().__init__(parent)
        self.config = config
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("设置")
        layout = QVBoxLayout(self)
        
        # 下载设置组
        download_group = QGroupBox("下载设置")
        download_layout = QVBoxLayout()
        
        # 默认保存路径
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("默认保存路径:"))
        self.path_edit = QLineEdit(self.config.default_save_path)
        path_layout.addWidget(self.path_edit)
        browse_btn = QPushButton("浏览")
        browse_btn.clicked.connect(self.browse_path)
        path_layout.addWidget(browse_btn)
        
        # 首选格式
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("首选格式:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems([
            "720p",      # 默认720p
            "480p",      # 清晰度适中
            "360p",      # 流畅
            "worst",     # 最低质量
            "best",      # 最高质量(需要大会员)
        ])
        self.format_combo.setCurrentText(self.config.preferred_format)
        format_layout.addWidget(self.format_combo)
        
        download_layout.addLayout(path_layout)
        download_layout.addLayout(format_layout)
        download_group.setLayout(download_layout)
        
        # 代理设置组
        proxy_group = QGroupBox("代理设置")
        proxy_layout = QVBoxLayout()
        
        self.enable_proxy = QCheckBox("启用代理")
        self.enable_proxy.setChecked(self.config.enable_proxy)
        
        proxy_input_layout = QHBoxLayout()
        proxy_input_layout.addWidget(QLabel("代理地址:"))
        self.proxy_edit = QLineEdit(self.config.proxy_url)
        proxy_input_layout.addWidget(self.proxy_edit)
        
        proxy_layout.addWidget(self.enable_proxy)
        proxy_layout.addLayout(proxy_input_layout)
        proxy_group.setLayout(proxy_layout)
        
        # 下载限制设置组
        limit_group = QGroupBox("下载限制")
        limit_layout = QVBoxLayout()
        
        # 最大并发数
        concurrent_layout = QHBoxLayout()
        concurrent_layout.addWidget(QLabel("最大并发下载数:"))
        self.concurrent_spin = QSpinBox()
        self.concurrent_spin.setRange(1, 10)
        self.concurrent_spin.setValue(self.config.max_concurrent_downloads)
        concurrent_layout.addWidget(self.concurrent_spin)
        
        # 速度限制
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("下载速度限制(KB/s):"))
        self.speed_spin = QSpinBox()
        self.speed_spin.setRange(0, 10000)
        self.speed_spin.setValue(self.config.download_speed_limit)
        self.speed_spin.setSpecialValueText("不限制")
        speed_layout.addWidget(self.speed_spin)
        
        limit_layout.addLayout(concurrent_layout)
        limit_layout.addLayout(speed_layout)
        limit_group.setLayout(limit_layout)
        
        # 界面设置组
        ui_group = QGroupBox("界面设置")
        ui_layout = QVBoxLayout()
        
        self.show_stats = QCheckBox("显示任务统计信息")
        self.show_stats.setChecked(self.config.show_task_stats)
        
        self.enable_notifications = QCheckBox("启用托盘通知")
        self.enable_notifications.setChecked(self.config.enable_tray_notifications)
        
        self.minimize_tray = QCheckBox("最小化到托盘")
        self.minimize_tray.setChecked(self.config.minimize_to_tray)
        
        ui_layout.addWidget(self.show_stats)
        ui_layout.addWidget(self.enable_notifications)
        ui_layout.addWidget(self.minimize_tray)
        ui_group.setLayout(ui_layout)
        
        # 按钮
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("保存")
        cancel_btn = QPushButton("取消")
        save_btn.clicked.connect(self.save_settings)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        
        # 添加到主布局
        layout.addWidget(download_group)
        layout.addWidget(proxy_group)
        layout.addWidget(limit_group)
        layout.addWidget(ui_group)
        layout.addLayout(btn_layout)
        
    def browse_path(self):
        path = QFileDialog.getExistingDirectory(self, "选择默认保存目录")
        if path:
            self.path_edit.setText(path)
            
    def save_settings(self):
        self.config.default_save_path = self.path_edit.text()
        self.config.preferred_format = self.format_combo.currentText()
        self.config.enable_proxy = self.enable_proxy.isChecked()
        self.config.proxy_url = self.proxy_edit.text()
        self.config.max_concurrent_downloads = self.concurrent_spin.value()
        self.config.download_speed_limit = self.speed_spin.value()
        self.config.show_task_stats = self.show_stats.isChecked()
        self.config.enable_tray_notifications = self.enable_notifications.isChecked()
        self.config.minimize_to_tray = self.minimize_tray.isChecked()
        
        self.config.save()
        self.accept() 