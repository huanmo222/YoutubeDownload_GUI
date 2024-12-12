import sqlite3
import os
from datetime import datetime
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class DownloadRecord:
    url: str
    filename: str
    save_path: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str = "pending"
    error_message: str = ""
    file_size: int = 0
    
class DownloadHistory:
    def __init__(self):
        self.db_path = os.path.join(os.path.expanduser("~"), ".video_downloader", "history.db")
        self._init_db()
        
    def _init_db(self):
        """初始化数据库"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS downloads (
                    url TEXT PRIMARY KEY,
                    filename TEXT,
                    save_path TEXT,
                    start_time TIMESTAMP,
                    end_time TIMESTAMP,
                    status TEXT,
                    error_message TEXT,
                    file_size INTEGER
                )
            """)
            
    def add_record(self, record: DownloadRecord):
        """添加下载记录"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO downloads
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record.url,
                record.filename,
                record.save_path,
                record.start_time.isoformat(),
                record.end_time.isoformat() if record.end_time else None,
                record.status,
                record.error_message,
                record.file_size
            ))
            
    def get_records(self, limit: int = 100) -> List[DownloadRecord]:
        """获取下载记录"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT * FROM downloads
                ORDER BY start_time DESC
                LIMIT ?
            """, (limit,))
            
            return [
                DownloadRecord(
                    url=row[0],
                    filename=row[1],
                    save_path=row[2],
                    start_time=datetime.fromisoformat(row[3]),
                    end_time=datetime.fromisoformat(row[4]) if row[4] else None,
                    status=row[5],
                    error_message=row[6],
                    file_size=row[7]
                )
                for row in cursor.fetchall()
            ]
            
    def update_status(self, url: str, status: str, error_message: str = ""):
        """更新下载状态"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE downloads
                SET status = ?, error_message = ?, end_time = ?
                WHERE url = ?
            """, (status, error_message, datetime.now().isoformat(), url)) 
            
    def clear_all(self):
        """清空所有历史记录"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM downloads")
            conn.execute("VACUUM")  # 清理数据库文件 