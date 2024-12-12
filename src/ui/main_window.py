from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QTableWidget, QTableWidgetItem,
    QLabel, QFileDialog, QHeaderView, QMessageBox,
    QProgressBar, QSystemTrayIcon, QMenu, QToolBar,
    QApplication, QStyle, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, QUrl
from PyQt6.QtGui import QColor, QIcon, QAction, QDesktopServices
import asyncio
import os
from functools import partial
from downloader import TaskStatus
from utils.config import AppConfig

class MainWindow(QMainWindow):
    def __init__(self, downloader):
        super().__init__()
        self.downloader = downloader
        self.config = AppConfig.load()
        self.notified_tasks = set()  # 添加已通知任务的集合
        
        # 加载样式表
        self.load_stylesheet()
        
        self.init_ui()
        
        # 恢复窗口位置和大小
        self.setGeometry(
            self.config.window_x,
            self.config.window_y,
            self.config.window_width,
            self.config.window_height
        )
        
        # 创建系统托盘图标
        self.create_tray_icon()
        
        # 创建定时器用于更新进度
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress)
        self.timer.timeout.connect(self.update_stats)
        self.timer.start(1000)
        
    def load_stylesheet(self):
        """加载样式表"""
        style_path = os.path.join("resources", "styles", "main.qss")
        if os.path.exists(style_path):
            with open(style_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
                
    def init_ui(self):
        self.setWindowTitle('视频下载器')
        self.setAcceptDrops(True)  # 启用拖放
        
        # 创建工具栏
        self.create_toolbar()
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 创建搜索区域
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索任务...")
        self.search_input.textChanged.connect(self.filter_tasks)
        search_layout.addWidget(self.search_input)
        
        # URL输入区域
        input_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("请输入视频URL")
        self.download_btn = QPushButton("下载")
        self.download_btn.clicked.connect(self.handle_download_click)
        
        input_layout.addWidget(self.url_input)
        input_layout.addWidget(self.download_btn)
        
        # 批量下载按钮
        self.batch_btn = QPushButton("批量下载")
        self.batch_btn.clicked.connect(self.handle_batch_download)
        input_layout.addWidget(self.batch_btn)
        
        # 创建任务列表
        self.task_table = QTableWidget(0, 6)
        self.task_table.setHorizontalHeaderLabels(["URL", "文件名", "进度", "速度", "剩余时间", "操作"])
        self.task_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.task_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.task_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.task_table.setSortingEnabled(True)  # 启用排序
        
        # 设置右键菜单
        self.task_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.task_table.customContextMenuRequested.connect(self.show_context_menu)
        
        # 添加到主布局
        layout.addLayout(search_layout)
        layout.addLayout(input_layout)
        layout.addWidget(self.task_table)
        
        # 添加状态栏
        self.status_bar = self.statusBar()
        self.stats_label = QLabel()
        self.status_bar.addWidget(self.stats_label)
        
        # 添加菜单栏
        self.create_menu_bar()
        
    def create_toolbar(self):
        """创建工具栏"""
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        
        # 添加工具栏按钮
        pause_all_action = QAction(QIcon.fromTheme("media-playback-pause"), "暂停所有", self)
        resume_all_action = QAction(QIcon.fromTheme("media-playback-start"), "继续所有", self)
        cancel_all_action = QAction(QIcon.fromTheme("process-stop"), "取消所有", self)
        
        toolbar.addAction(pause_all_action)
        toolbar.addAction(resume_all_action)
        toolbar.addAction(cancel_all_action)
        
        # 绑定事件
        pause_all_action.triggered.connect(self.pause_all_tasks)
        resume_all_action.triggered.connect(self.resume_all_tasks)
        cancel_all_action.triggered.connect(self.cancel_all_tasks)
        
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu('文件')
        
        # 创建动作
        new_action = QAction('新建下载', self)
        new_action.setShortcut('Ctrl+N')
        new_action.triggered.connect(self.handle_download_click)
        
        batch_action = QAction('批量下载', self)
        batch_action.setShortcut('Ctrl+B')
        batch_action.triggered.connect(self.handle_batch_download)
        
        exit_action = QAction('退出', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        
        # 添加到菜单
        file_menu.addAction(new_action)
        file_menu.addAction(batch_action)
        file_menu.addSeparator()
        file_menu.addAction(exit_action)
        
        # 任务菜单
        task_menu = menubar.addMenu('任务')
        
        pause_all_action = QAction('全部暂停', self)
        pause_all_action.triggered.connect(self.pause_all_tasks)
        
        resume_all_action = QAction('全部继续', self)
        resume_all_action.triggered.connect(self.resume_all_tasks)
        
        cancel_all_action = QAction('全部取消', self)
        cancel_all_action.triggered.connect(self.cancel_all_tasks)
        
        task_menu.addAction(pause_all_action)
        task_menu.addAction(resume_all_action)
        task_menu.addAction(cancel_all_action)
        
        # 设置菜单
        settings_menu = menubar.addMenu('设置')
        
        preferences_action = QAction('首选项', self)
        preferences_action.triggered.connect(self.show_settings)
        
        history_action = QAction('下载历史', self)
        history_action.triggered.connect(self.show_history)
        
        settings_menu.addAction(preferences_action)
        settings_menu.addAction(history_action)
        
    def create_tray_icon(self):
        """创建系统托盘图标"""
        self.tray_icon = QSystemTrayIcon(self)
        
        # 创建默认图标
        icon = self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        self.tray_icon.setIcon(icon)
        
        self.tray_icon.setToolTip("视频下载器")
        self.tray_icon.show()
        
    def show_context_menu(self, pos):
        """显示右键菜单"""
        menu = QMenu(self)
        
        # 获取选中的行
        rows = set(item.row() for item in self.task_table.selectedItems())
        if not rows:
            return
            
        # 添加菜单项
        pause_action = menu.addAction("暂停")
        cancel_action = menu.addAction("取消")
        menu.addSeparator()
        copy_url_action = menu.addAction("复制URL")
        open_folder_action = menu.addAction("打开文件夹")
        
        # 显示菜单
        action = menu.exec(self.task_table.mapToGlobal(pos))
        if not action:
            return
            
        # 处理菜单动作
        for row in rows:
            url = self.task_table.item(row, 0).text()
            if action == pause_action:
                self.handle_pause_click(url)
            elif action == cancel_action:
                self.handle_cancel_click(url)
            elif action == copy_url_action:
                QApplication.clipboard().setText(url)
            elif action == open_folder_action:
                task = self.downloader.get_task(url)
                if task and task.save_path:
                    QDesktopServices.openUrl(QUrl.fromLocalFile(task.save_path))
                    
    def filter_tasks(self):
        """过滤任务列表"""
        search_text = self.search_input.text().lower()
        for row in range(self.task_table.rowCount()):
            hidden = True
            for col in range(self.task_table.columnCount() - 1):  # 跳过操作列
                item = self.task_table.item(row, col)
                if item and search_text in item.text().lower():
                    hidden = False
                    break
            self.task_table.setRowHidden(row, hidden)
            
    def pause_all_tasks(self):
        """暂停所有任务"""
        for url in self.downloader.tasks:
            self.downloader.pause_task(url)
            
    def resume_all_tasks(self):
        """继续所有任务"""
        for url in self.downloader.tasks:
            self.downloader.resume_task(url)
            
    def cancel_all_tasks(self):
        """取消所有任务"""
        if QMessageBox.question(
            self,
            "确认",
            "确定要取消所有下载任务吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            for url in list(self.downloader.tasks.keys()):
                self.downloader.cancel_task(url)
                
    def dragEnterEvent(self, event):
        """处理拖入事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            
    def dropEvent(self, event):
        """处理放下事件"""
        urls = []
        for url in event.mimeData().urls():
            if url.isValid():
                urls.append(url.toString())
                
        if urls:
            save_path = QFileDialog.getExistingDirectory(self, "选择保存目录")
            if save_path:
                for url in urls:
                    self.add_download_task(url, save_path)
                    
    def update_stats(self):
        """更新任务统计信息"""
        if not self.config.show_task_stats:
            self.stats_label.clear()
            return
            
        total = self.task_table.rowCount()
        active = sum(1 for task in self.downloader.tasks.values() 
                    if task.status == TaskStatus.DOWNLOADING)
        completed = sum(1 for task in self.downloader.tasks.values() 
                       if task.status == TaskStatus.COMPLETED)
        failed = sum(1 for task in self.downloader.tasks.values() 
                    if task.status == TaskStatus.ERROR)
        
        stats = f"总任务: {total} | 下载中: {active} | 已完成: {completed} | 失败: {failed}"
        self.stats_label.setText(stats)
        
    def closeEvent(self, event):
        """处理窗口关闭事件"""
        if self.config.minimize_to_tray and self.isVisible():
            event.ignore()
            self.hide()
            self.tray_icon.showMessage(
                "提示",
                "程序已最小化到系统托盘",
                QSystemTrayIcon.MessageIcon.Information,
                2000
            )
        else:
            # 保存窗口位置和大小
            geometry = self.geometry()
            self.config.window_x = geometry.x()
            self.config.window_y = geometry.y()
            self.config.window_width = geometry.width()
            self.config.window_height = geometry.height()
            self.config.save()
            
            super().closeEvent(event)

    def handle_download_click(self):
        """处理下载按钮点击事件"""
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "提示", "请输入视频URL")
            return
        
        # 选择保存目录
        save_path = QFileDialog.getExistingDirectory(self, "选择保存目录")
        if not save_path:
            return
        
        # 添加下载任务
        self.add_download_task(url, save_path)
        
        # 清空输入框
        self.url_input.clear()

    def handle_batch_download(self):
        """处理批量下载"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择URL列表文件",
            "",
            "文本文件 (*.txt);;所有文件 (*.*)"
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                urls = [line.strip() for line in f if line.strip()]
        except Exception as e:
            QMessageBox.critical(self, "错误", f"读取文件失败: {str(e)}")
            return
        
        if not urls:
            QMessageBox.warning(self, "提示", "文件中没有找到URL")
            return
        
        # 选择保存目录
        save_path = QFileDialog.getExistingDirectory(self, "选择保存目录")
        if not save_path:
            return
        
        # 添加所有下载任务
        for url in urls:
            self.add_download_task(url, save_path)

    def add_download_task(self, url: str, save_path: str):
        """添加下载任务"""
        row = self.task_table.rowCount()
        self.task_table.insertRow(row)
        
        # 设置任务信息
        self.task_table.setItem(row, 0, QTableWidgetItem(url))
        self.task_table.setItem(row, 1, QTableWidgetItem(""))
        
        # 创建进度条
        progress_bar = QProgressBar()
        progress_bar.setRange(0, 100)
        self.task_table.setCellWidget(row, 2, progress_bar)
        
        self.task_table.setItem(row, 3, QTableWidgetItem(""))
        self.task_table.setItem(row, 4, QTableWidgetItem(""))
        
        # 创建操作按钮容器
        btn_widget = QWidget()
        layout = QHBoxLayout(btn_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建按钮
        pause_btn = QPushButton("暂停")
        cancel_btn = QPushButton("取消")
        
        # 设置按钮大小策略
        pause_btn.setFixedSize(45, 24)
        cancel_btn.setFixedSize(45, 24)
        
        # 添加按钮到布局
        layout.addWidget(pause_btn)
        layout.addWidget(cancel_btn)
        
        # 设置按钮容器到表格
        self.task_table.setCellWidget(row, 5, btn_widget)
        
        # 绑定按钮事件
        pause_btn.clicked.connect(partial(self.handle_pause_click, url))
        cancel_btn.clicked.connect(partial(self.handle_cancel_click, url))
        
        # 启动下载任务
        asyncio.create_task(self.start_download(url, save_path))

    async def start_download(self, url: str, save_path: str):
        """开始下载任务"""
        try:
            await self.downloader.download(url, save_path)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"下载失败: {str(e)}")

    def handle_pause_click(self, url: str):
        """处理暂停按钮点击"""
        task = self.downloader.get_task(url)
        if task and task.status == TaskStatus.DOWNLOADING:
            self.downloader.pause_task(url)
            sender = self.sender()
            sender.setText("继续")
        else:
            self.downloader.resume_task(url)
            sender.setText("暂停")

    def handle_cancel_click(self, url: str):
        """处理取消按钮点"""
        if QMessageBox.question(
            self,
            "确认",
            "确定要取消该下载任务吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            self.downloader.cancel_task(url)

    def update_progress(self):
        """更新所有任务的进度显示"""
        for row in range(self.task_table.rowCount()):
            url = self.task_table.item(row, 0).text()
            task = self.downloader.get_task(url)
            if task:
                # 更新文件名
                self.task_table.setItem(row, 1, QTableWidgetItem(task.filename))
                
                # 更新进度条
                progress_bar = self.task_table.cellWidget(row, 2)
                if not progress_bar:
                    progress_bar = QProgressBar()
                    progress_bar.setRange(0, 100)
                    self.task_table.setCellWidget(row, 2, progress_bar)
                progress_bar.setValue(int(task.progress))
                
                # 更新速度
                self.task_table.setItem(row, 3, QTableWidgetItem(task.speed))
                
                # 更新剩余时间
                self.task_table.setItem(row, 4, QTableWidgetItem(task.eta))
                
                # 根据状态设置颜色
                color = self._get_status_color(task.status)
                for col in [0, 1, 3, 4]:  # 跳过进度条列
                    item = self.task_table.item(row, col)
                    if item:
                        item.setForeground(color)
                        
                # 控制按钮显示
                btn_container = self.task_table.cellWidget(row, 5)
                if btn_container:
                    # 根据任务状态控制按钮容器的可见性
                    if task.status in [TaskStatus.DOWNLOADING, TaskStatus.PAUSED, TaskStatus.PENDING]:
                        btn_container.setVisible(True)
                    else:  # 完成、取消或错误状态
                        btn_container.setVisible(False)
                
                # 下载完成时显示通知（只提示一次）
                if task.status == TaskStatus.COMPLETED and url not in self.notified_tasks:
                    self.tray_icon.showMessage(
                        "下载完成",
                        f"文件 {task.filename} 已下载完成",
                        QSystemTrayIcon.MessageIcon.Information,
                        3000
                    )
                    self.notified_tasks.add(url)  # 添加到已通知集合

    def _get_status_color(self, status: TaskStatus) -> QColor:
        """获取任务状态对应的颜色"""
        colors = {
            TaskStatus.DOWNLOADING: QColor(0, 128, 0),  # 绿色
            TaskStatus.COMPLETED: QColor(0, 0, 255),    # 蓝色
            TaskStatus.ERROR: QColor(255, 0, 0),        # 红色
            TaskStatus.PAUSED: QColor(128, 128, 0),     # 黄色
            TaskStatus.CANCELLED: QColor(128, 128, 128), # 灰色
            TaskStatus.PENDING: QColor(0, 0, 0),        # 黑色
        }
        return colors.get(status, QColor(0, 0, 0))

    def show_settings(self):
        """显示设置对话框"""
        from ui.settings_dialog import SettingsDialog
        dialog = SettingsDialog(self.config, self)
        if dialog.exec():
            # 更新下载器配置
            self.downloader.update_config(self.config)

    def show_history(self):
        """显示下载历史"""
        from ui.history_dialog import HistoryDialog
        dialog = HistoryDialog(
            redownload_callback=self.add_download_task,
            parent=self
        )
        dialog.exec()