# 项目概览

## 项目背景

FF Intelligent Neo 是一款桌面端 FFmpeg 批量处理工具，旨在为视频工作者提供一个直观、高效的批量转码解决方案。用户无需在命令行中手动输入 FFmpeg 命令，通过图形界面即可完成复杂的视频处理任务。

### 核心价值

- **降低使用门槛** - 将复杂的 FFmpeg 命令行操作转化为图形化配置
- **批量处理** - 支持一次性添加多个文件，排队自动处理
- **精细控制** - 每个任务可独立暂停、恢复、停止、重试
- **实时反馈** - 进度条、速度、FPS、预估剩余时间等实时显示
- **配置复用** - 通过预设系统保存和复用常用配置

## 目标用户

| 用户类型 | 使用场景 |
|---------|---------|
| 视频创作者 | 批量转码、压缩、添加水印 |
| 直播录像处理 | 批量转换录制文件格式 |
| 媒体资产管理者 | 统一转码标准、批量处理 |
| 个人用户 | 简单的视频格式转换 |

## 版本历史

### v1.0.0 (MVP)

- 单页面应用
- 基础的文件添加和 FFmpeg 执行
- 简单的命令行预览
- 一次性批量执行（无独立任务控制）

### v2.0.0 (当前版本)

- 架构全面重构：从单页面升级为多页面 Vue Router 架构
- 任务系统升级：从一次性批量执行升级为可控任务队列
- 新增任务独立控制（暂停/恢复/停止/重试）
- 新增批量操作（全部暂停/全部恢复/全部停止）
- 新增结构化 FFmpeg 配置系统（转码参数 + 滤镜链）
- 新增预设管理系统（内置预设 + 用户预设）
- 新增应用设置持久化
- 新增任务队列状态持久化与启动恢复
- 新增实时命令预览与配置验证
- 新增进程级暂停/恢复（跨平台）
- 新增窗口关闭时强制终止所有进程

## 技术栈详解

### 后端

| 技术 | 版本 | 用途 |
|-----|------|-----|
| Python | 3.11+ | 后端运行时 |
| pywebview | >=6.0 | 桌面窗口容器，原生 WebView 封装 |
| static-ffmpeg | - | FFmpeg 二进制文件自动管理 |
| loguru | >=0.7 | 日志框架 |
| PyInstaller | >=6.19 | 跨平台可执行文件打包 |

### 前端

| 技术 | 版本 | 用途 |
|-----|------|-----|
| Vue 3 | ^3.5.0 | UI 框架（Composition API） |
| TypeScript | ~5.7.0 | 类型安全 |
| Vue Router | 4 | 客户端路由（Hash 模式） |
| Tailwind CSS | ^4.1.0 | 原子化 CSS 框架 |
| DaisyUI | ^5.0.0 | UI 组件库 |
| Vite | ^6.0.0 | 构建工具 + 开发服务器 |

### 工具链

| 工具 | 用途 |
|-----|-----|
| uv | Python 包管理器 |
| bun | Node.js 包管理器 |
| vue-tsc | TypeScript 类型检查 |
| PyInstaller | 可执行文件打包 |

### 架构选择说明

- **pywebview 而非 Electron**: 更小的打包体积，使用系统原生 WebView，无需打包 Chromium
- **Vue 3 Composition API + Composables**: 替代 Pinia/Vuex，更轻量的状态管理方案
- **PyWebVue 自研桥接层**: 提供 `@expose` 装饰器和事件系统，实现前后端双向通信
- **ThreadPoolExecutor**: 任务并行执行，配合 `threading.Event` 实现取消控制

## 开发环境搭建

### 前置条件

1. **Python 3.11+** - 运行时环境
2. **uv** - Python 包管理器（[安装指南](https://github.com/astral-sh/uv)）
3. **bun** - Node.js 包管理器（[安装指南](https://bun.sh/)）

### 安装步骤

```bash
# 1. 克隆项目
git clone <repository-url>
cd ff-intelligent-neo

# 2. 安装 Python 依赖
uv sync

# 3. 安装前端依赖
cd frontend && bun install && cd ..
```

### 开发模式

```bash
# 启动开发服务器（前端热重载 + 后端热启动）
uv run dev.py
```

开发模式下：
- 前端通过 Vite 开发服务器提供（支持热模块替换）
- 后端 Python 代码修改后需手动重启
- FFmpeg 首次运行时自动下载

### 构建打包

```bash
# 构建可执行文件
uv run build.py
```

构建流程：
1. 前端构建（Vite 打包 Vue 应用）
2. FFmpeg 预下载（确保二进制文件就位）
3. PyInstaller 打包（生成单目录可执行文件）

构建产物位于 `dist/` 目录。

## 数据存储

应用数据存储于系统用户数据目录（`%APPDATA%` on Windows, `~/Library/Application Support` on macOS, `~/.local/share` on Linux）：

| 文件 | 用途 |
|-----|-----|
| `ff-intelligent-neo/settings.json` | 应用设置 |
| `ff-intelligent-neo/queue_state.json` | 任务队列持久化状态 |
| `ff-intelligent-neo/presets/*.json` | 用户自定义预设 |

## 已知问题与未来规划

### 已知问题 (v2.0.0)

- Windows 暂停进程需要管理员权限（使用 `NtSuspendProcess`）
- 暂停时进程缓冲区可能溢出（长时间暂停）
- 大队列（100+ 任务）JSON 序列化可能有性能影响
- 多实例同时运行可能导致队列状态文件损坏

### 规划中 (v2.1.0)

- 多平台兼容性改进
- 命令构建器功能完善
- 任务完成日志显示优化
- 水印路径拖拽文件输入
- FFmpeg 版本指示器实时更新
- 浅色/深色主题支持
- i18n 多语言支持
