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

### v2.0.0

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

### v2.1.0 / v2.1.1

- 命令构建器完善（Phase 3 全系列）、页面拆分（A/V Mix、Merge、Custom）
- Clip 剪辑、状态机 Reset、国际化（i18n）、多平台支持
- 数据目录统一、性能优化（命令预览、异步探测）

### v2.2.0

- 自动剪辑（auto-editor）集成：自动检测、命令预览、任务执行
- FFprobe 分析功能：全屏拖拽 + 点击选择输入，解析结果全量显示
- macOS 支持：FFmpeg/FFprobe 自动下载、Homebrew 路径检测
- 安全加固：路径穿越防护、原子写入、下载校验

### v2.2.1

- 前后端全面安全审计与修复
- 线程安全：Task 模型加锁、队列原子写入、初始化可重入锁
- 前端内存泄漏修复：定时器清理、作用域销毁、事件监听生命周期
- 类型安全强化：消除不安全类型断言、事件字段校验、Bridge 超时
- macOS FFprobe 路径检测修复
- "重置全部"按钮移至预设选项栏

### v2.2.2

- macOS .app 应用包打包支持（PyInstaller BUNDLE）
- Vue 全局错误处理器（main.ts）
- FileDropInput 无效属性修复（空字符串属性导致 InvalidCharacterError）
- auto-editor 初始化竞态修复（状态闪烁问题）
- 打包版版本号显示修复

### v2.2.3 (当前版本)

- 剪辑模式默认改为 cut（时间范围），新增不精准剪辑选项（cut_no_accurate / extract_no_accurate）
- 剪辑配置解除与转码/滤镜的互斥，允许合并应用
- 自定义命令输入/输出选项自动识别与排序（`_INPUT_OPTIONS` 白名单）
- 剪辑命令构建多项修复：file_duration 传递、验证放宽、子配置合并
- 剪辑时间输入范围自动截断 + 一键清空
- M4A 输出格式支持

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

## 版本变更索引

| 版本 | 新增/修改内容 |
|------|---------|
| v2.0.0 | 架构全面重构：多页面 Vue Router、任务队列可控、结构化 FFmpeg 配置、预设管理、应用设置持久化 |
| v2.1.0 | 命令构建器完善（Phase 3）、页面拆分（A/V Mix、Merge、Custom）、Clip 剪辑、状态机 Reset |
| v2.1.1 | 国际化（i18n）、多平台支持、数据目录统一、性能优化（命令预览、异步探测） |
| Phase 3.5 | 编码器质量自动填充、片头片尾、自定义命令、分辨率/时间输入拆分 |
| Phase 3.5.1 | 滤镜互斥修复、路径引用修复、音频码率默认调整 |
| Phase 3.5.2 | SplitDropZone 全屏拖拽、Merge 独立提交、Intro/Outro 移至 Config 页 |
| Phase 4 | 国际化架构、core/paths.py 数据目录、平台检测增强 |
| Phase 5 | 队列表格布局重构、打开文件夹功能、任务状态变更重新获取、按钮尺寸统一 |
| v2.1.1 | useCommandPreview 优化、preview_command API、Bridge 事件类型安全、前端错误反馈 |
| v2.2.0 | 自动剪辑（auto-editor）集成、FFprobe 分析、macOS FFmpeg 下载、安全加固（路径穿越/原子写入/下载校验） |
| v2.2.1 | 前后端安全审计：线程安全 Task/Queue、内存泄漏修复、类型安全强化、Bridge 超时、macOS ffprobe 路径修复 |
| v2.2.2 | macOS .app 打包、Vue 全局错误处理、FileDropInput 属性修复、auto-editor 竞态修复、打包版版本号修复 |
| v2.2.3 | 剪辑默认 cut 模式 + 不精准选项、剪辑与转码合并、自定义命令选项自动排序、命令构建多项修复、M4A 格式 |

## 已知问题与未来规划

### 已知问题 (v2.0.0)

- Windows 暂停进程需要管理员权限（使用 `NtSuspendProcess`）
- 暂停时进程缓冲区可能溢出（长时间暂停）
- 大队列（100+ 任务）JSON 序列化可能有性能影响
- 多实例同时运行可能导致队列状态文件损坏

### 已实现 (v2.1.0 ~ v2.2.3)

以下功能已在 v2.1.0 ~ v2.2.3 中实现：

- [x] 多平台兼容性改进（Phase 4 平台检测）
- [x] 命令构建器功能完善（Phase 3 全系列）
- [x] 任务完成日志显示优化（日志可见性规则）
- [x] 水印路径拖拽文件输入（FileDropInput / SplitDropZone）
- [x] FFmpeg 版本指示器实时更新（ffmpeg_version_changed 事件）
- [x] 浅色/深色主题支持（useTheme.ts）
- [x] i18n 多语言支持（Phase 4）
- [x] 自动剪辑（auto-editor）集成（v2.2.0）
- [x] FFprobe 音视频参数分析（v2.2.0）
- [x] macOS 平台支持：FFmpeg/FFprobe 自动下载、.app 打包（v2.2.0 ~ v2.2.2）
- [x] 安全加固：线程安全、原子写入、路径穿越防护（v2.2.0 ~ v2.2.1）
- [x] 前端稳定性：内存泄漏修复、类型安全、Vue 全局错误处理（v2.2.1 ~ v2.2.2）
- [x] 剪辑模式增强：默认 cut、不精准选项、与转码合并（v2.2.3）
- [x] 自定义命令输入/输出选项自动排序（v2.2.3）
- [x] M4A 输出格式支持（v2.2.3）

### 待规划

- 大队列（100+ 任务）性能优化
- 多实例运行队列状态保护
- 暂停时缓冲区溢出处理
