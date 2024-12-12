import yt_dlp
import asyncio
from typing import Optional, Callable, Dict, List
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
from utils.config import AppConfig
from utils.history import DownloadHistory, DownloadRecord
import os

class TaskStatus(Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    ERROR = "error"
    PAUSED = "paused"
    CANCELLED = "cancelled"

@dataclass
class DownloadTask:
    url: str
    save_path: str
    status: TaskStatus = TaskStatus.PENDING
    progress: float = 0
    speed: str = ""
    filename: str = ""
    error_message: str = ""
    start_time: Optional[datetime] = None
    eta: str = ""
    total_bytes: int = 0
    downloaded_bytes: int = 0
    cancel_event: asyncio.Event = None
    
    def __post_init__(self):
        self.cancel_event = asyncio.Event()

class VideoDownloader:
    def __init__(self):
        self.tasks: Dict[str, DownloadTask] = {}
        self.history = DownloadHistory()
        self.max_retries = 3
        self.active_downloads = 0
        self.download_queue = asyncio.Queue()
        self.download_semaphore = asyncio.Semaphore(3)
        
        self.ydl_opts = {
            'format': 'best',  # 使用最佳的单一格式，而不是分离的音视频
            'progress_hooks': [self._progress_hook],
            'outtmpl': '%(title)s.%(ext)s',
        }
        
        # 启动队列处理器
        asyncio.create_task(self._process_queue())
        
    async def _process_queue(self):
        """处理下载队列"""
        while True:
            url, save_path = await self.download_queue.get()
            
            async with self.download_semaphore:
                try:
                    await self._do_download(url, save_path)
                except Exception as e:
                    # 错误已在_do_download中处理
                    pass
                finally:
                    self.download_queue.task_done()
                    
    async def download(self, url: str, save_path: str) -> None:
        """添加下载任务到队列"""
        task = self.get_task(url) or self.add_task(url, save_path)
        await self.download_queue.put((url, save_path))
        
    async def _do_download(self, url: str, save_path: str) -> None:
        """实际的下载实现"""
        task = self.get_task(url)
        if not task:
            return
            
        # 先列出可用格式
        formats = await self.list_formats(url)
        print("Available formats:")
        for fmt in formats:
            print(fmt)
        
        task.status = TaskStatus.DOWNLOADING
        task.start_time = datetime.now()
        
        # 创建下载记录
        record = DownloadRecord(
            url=url,
            filename="",
            save_path=save_path,
            start_time=task.start_time
        )
        
        retries = 0
        while retries < self.max_retries:
            try:
                # 配置下载选项
                opts = dict(self.ydl_opts)
                opts['outtmpl'] = f"{save_path}/%(title)s.%(ext)s"
                
                # 创建下载器实例
                with yt_dlp.YoutubeDL(opts) as ydl:
                    # 检查取消事件
                    if task.cancel_event.is_set():
                        task.status = TaskStatus.CANCELLED
                        record.status = "cancelled"
                        self.history.add_record(record)
                        return
                    
                    # 开始下载
                    await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: ydl.download([url])
                    )
                    
                    if not task.cancel_event.is_set():
                        task.status = TaskStatus.COMPLETED
                        record.status = "completed"
                        record.filename = task.filename
                        record.end_time = datetime.now()
                        self.history.add_record(record)
                        return
                    
            except asyncio.CancelledError:
                task.status = TaskStatus.CANCELLED
                record.status = "cancelled"
                self.history.add_record(record)
                raise
                
            except Exception as e:
                retries += 1
                if retries >= self.max_retries:
                    task.status = TaskStatus.ERROR
                    task.error_message = str(e)
                    record.status = "error"
                    record.error_message = str(e)
                    record.end_time = datetime.now()
                    self.history.add_record(record)
                    raise
                else:
                    # 等待一段时间后重试
                    await asyncio.sleep(2 ** retries)  # 指数退避
                    continue
    
    def add_task(self, url: str, save_path: str) -> DownloadTask:
        """添加下载任务到队列"""
        task = DownloadTask(url=url, save_path=save_path)
        self.tasks[url] = task
        return task
    
    def get_task(self, url: str) -> Optional[DownloadTask]:
        """获取指定任务信息"""
        return self.tasks.get(url)
    
    def pause_task(self, url: str) -> None:
        """暂停下载任务"""
        if url in self.tasks:
            self.tasks[url].status = TaskStatus.PAUSED
    
    def resume_task(self, url: str) -> None:
        """恢复下载任务"""
        if url in self.tasks:
            self.tasks[url].status = TaskStatus.PENDING
    
    def cancel_task(self, url: str) -> None:
        """取消下载任务"""
        if url in self.tasks:
            task = self.tasks[url]
            task.cancel_event.set()
            task.status = TaskStatus.CANCELLED
    
    def update_config(self, config: 'AppConfig'):
        """更新下载器配置"""
        self.ydl_opts.update({
            'format': config.preferred_format,
            'ratelimit': config.download_speed_limit * 1024 if config.download_speed_limit > 0 else None,
        })
        
        if config.enable_proxy:
            self.ydl_opts['proxy'] = config.proxy_url
        else:
            self.ydl_opts.pop('proxy', None)
            
        # 更���并发数限制
        self.download_semaphore = asyncio.Semaphore(config.max_concurrent_downloads)
    
    def _progress_hook(self, d):
        """处理下载进度回调"""
        if d['status'] == 'downloading':
            url = d['info_dict']['webpage_url']
            if url in self.tasks:
                task = self.tasks[url]
                
                # 更新下载进度
                if 'total_bytes' in d:
                    task.total_bytes = d['total_bytes']
                    task.downloaded_bytes = d['downloaded_bytes']
                    task.progress = (d['downloaded_bytes'] / d['total_bytes']) * 100
                elif 'total_bytes_estimate' in d:
                    task.total_bytes = d['total_bytes_estimate']
                    task.downloaded_bytes = d['downloaded_bytes']
                    task.progress = (d['downloaded_bytes'] / d['total_bytes_estimate']) * 100
                
                # 更新下载速度
                if 'speed' in d and d['speed']:
                    task.speed = f"{d['speed']/1024/1024:.1f} MB/s"
                else:
                    task.speed = "计算中..."
                
                # 更新预计剩余时间
                if 'eta' in d and d['eta']:
                    task.eta = f"{d['eta']//60}分{d['eta']%60}秒"
                else:
                    task.eta = "计算中..."
                
                # 更新文件名
                if 'filename' in d:
                    task.filename = os.path.basename(d['filename'])
                    
        elif d['status'] == 'finished':
            url = d['info_dict']['webpage_url']
            if url in self.tasks:
                task = self.tasks[url]
                task.progress = 100
                task.speed = "完成"
                task.eta = "0秒"
                if 'filename' in d:
                    task.filename = os.path.basename(d['filename'])
    
    async def list_formats(self, url: str) -> List[str]:
        """列出视频可用的格式"""
        formats = []
        opts = dict(self.ydl_opts)
        opts['listformats'] = True
        
        with yt_dlp.YoutubeDL(opts) as ydl:
            try:
                info = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: ydl.extract_info(url, download=False)
                )
                if info and 'formats' in info:
                    for f in info['formats']:
                        format_str = f"{f.get('format_id', 'N/A')} - {f.get('format', 'Unknown')}"
                        formats.append(format_str)
            except Exception as e:
                print(f"获取格式列表失败: {e}")
        
        return formats