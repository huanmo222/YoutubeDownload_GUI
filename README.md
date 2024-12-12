# 视频下载器

一个简单的视频下载工具，支持YouTube、Bilibili等平台。

## 功能特点

- 支持多个视频平台
- 多任务并发下载
- 下载进度显示
- 下载历史记录
- 代理设置支持

## 安装

1. 克隆仓库： 
bash
git clone https://github.com/yourusername/video-downloader.git
cd video-downloader

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 安装 ffmpeg：

Windows:
- 下载 ffmpeg: https://www.gyan.dev/ffmpeg/builds/
- 解压并将 bin 目录添加到系统环境变量 PATH 中

Linux:
```bash
sudo apt update
sudo apt install ffmpeg
```

MacOS:
```bash
brew install ffmpeg
```

## 运行

```bash
python src/main.py
```

## 使用说明

1. 输入视频URL，点击"下载"按钮开始下载
2. 支持批量下载：点击"批量下载"按钮，选择包含URL列表的文本文件
3. 可以通过设置菜单配置下载选项
4. 支持任务的暂停、继续和取消操作