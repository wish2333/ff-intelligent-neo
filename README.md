# FF Intelligent

基于 FFmpeg 的批量媒体处理桌面工具，提供直观的 GUI 界面，支持批量转码、预设管理、实时进度监控。

## 功能特性

- **批量处理** — 多文件并行转码，可配置工作线程数
- **预设系统** — 内置常用转码预设（MP3、AAC、MP4 封装、音频提取），支持自定义预设
- **实时进度** — 转码进度实时展示，包含速度、剩余时间、状态
- **文件管理** — 自动提取媒体文件元数据（编码格式、分辨率、时长等）
- **跨平台** — 支持 Windows、macOS、Linux
- **Android** — 可通过 Buildozer 构建 Android APK

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3.10+ / pywebview |
| 前端 | Vue 3 + TypeScript + Vite |
| UI | Tailwind CSS + DaisyUI |
| 桥接 | PyWebVue（Python ↔ Vue 通信） |
| 打包 | PyInstaller（Desktop）/ Buildozer（Android） |

## 快速开始

### 环境要求

- Python >= 3.10
- [uv](https://github.com/astral-sh/uv)（包管理）
- [bun](https://bun.sh/) / npm / yarn（前端构建，任选其一）

### 开发

```bash
# 安装依赖
uv sync

# 安装前端依赖并构建
cd frontend && bun install && bun run build && cd ..

# 启动应用
uv run main.py
```

### 构建

```bash
# Desktop — onedir 模式（推荐，启动快）
uv run build.py

# Desktop — onefile 模式（单文件，便于分发）
uv run build.py --onefile

# Android APK（需 macOS 或 Linux）
uv run build.py --android

# 清理构建产物
uv run build.py --clean
```

构建时会自动下载对应平台的 FFmpeg 二进制并打包进产物，无需用户手动安装。

## 内置预设

| 预设 | 说明 |
|------|------|
| Audio to MP3 | 转码为 MP3 320kbps |
| Audio to AAC | 转码为 AAC 256kbps（M4A 容器） |
| Remux to MP4 | 快速封装为 MP4（流拷贝，无需重编码） |
| Extract Audio | 提取为无损 WAV |

## 项目结构

```
ff-intelligent-mvp/
├── main.py                # 应用入口
├── build.py               # 自动化构建脚本
├── app.spec               # PyInstaller 打包配置
├── pyproject.toml         # 项目配置与依赖
├── core/                  # 核心业务模块
│   ├── models.py          # 数据模型
│   ├── batch_runner.py    # 批量转码调度
│   ├── ffmpeg_runner.py   # 单次 FFmpeg 执行
│   ├── ffmpeg_setup.py    # FFmpeg 二进制管理
│   ├── preset_manager.py  # 预设管理
│   ├── file_info.py       # 媒体文件元数据提取
│   ├── app_info.py        # 应用信息与版本检测
│   └── logging.py         # 日志配置
├── frontend/              # Vue.js 前端
├── presets/               # 内置预设
├── scripts/               # 构建辅助脚本
│   └── pre_build.py       # FFmpeg 预下载脚本
└── docs/                  # 文档
```

## License

MIT
