import json
import os
from dataclasses import dataclass, asdict
from typing import Optional

@dataclass
class AppConfig:
    # 下载设置
    default_save_path: str = ""
    preferred_format: str = "best"
    
    # 代理设置
    enable_proxy: bool = False
    proxy_url: str = ""
    
    # 窗口设置
    window_x: int = 100
    window_y: int = 100
    window_width: int = 1000
    window_height: int = 600
    
    # 下载限制
    max_concurrent_downloads: int = 3
    download_speed_limit: int = 0  # 0表示不限速，单位KB/s
    
    # 界面设置
    show_task_stats: bool = True
    enable_tray_notifications: bool = True
    minimize_to_tray: bool = True
    
    @classmethod
    def load(cls) -> 'AppConfig':
        """从配置文件加载配置"""
        config_path = os.path.join(os.path.expanduser("~"), ".video_downloader", "config.json")
        
        if not os.path.exists(config_path):
            return cls()
            
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return cls(**data)
        except Exception:
            return cls()
            
    def save(self):
        """保存配置到文件"""
        config_dir = os.path.join(os.path.expanduser("~"), ".video_downloader")
        os.makedirs(config_dir, exist_ok=True)
        
        config_path = os.path.join(config_dir, "config.json")
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(asdict(self), f, indent=2) 