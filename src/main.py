import sys
import asyncio
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow
from downloader import VideoDownloader

async def main():
    app = QApplication(sys.argv)
    
    # 创建下载器实例
    downloader = VideoDownloader()
    
    # 创建主窗口
    window = MainWindow(downloader)
    window.show()
    
    # 创建事件循环
    while True:
        app.processEvents()
        await asyncio.sleep(0.1)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0) 