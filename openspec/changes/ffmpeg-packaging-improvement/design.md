## Context

当前项目使用 `static-ffmpeg` 包在运行时下载 FFmpeg 二进制文件。该包的工作机制是：首次调用 `static_ffmpeg.add_paths()` 时，从 GitHub Releases 下载对应平台的 FFmpeg 压缩包并解压到包的缓存目录。

**当前状态：**
- `core/ffmpeg_setup.py` 中 `ensure_ffmpeg()` 调用 `static_ffmpeg.add_paths()` 触发下载
- `app.spec` 和 `_generate_onefile_spec()` 的 `binaries` 均为空列表
- 开发环境依赖 `static-ffmpeg`，生产环境也依赖运行时下载

**约束条件：**
- 桌面端需要支持 macOS、Windows、Linux 三平台
- 构建工具为 `uv` + PyInstaller
- FFmpeg 版本需保持与 preset 命令模板的兼容性

> **注意：** Android 端方案已搁置，归档于 `docs/shelved/android-ffmpeg-support.md`。

## Goals / Non-Goals

**Goals:**
- 构建阶段预下载 FFmpeg 并打包进最终产物，用户无需联网即可使用
- 开发环境保持现有体验不变
- Desktop 三平台（macOS/Windows/Linux）均支持

**Non-Goals:**
- 不替换 `static-ffmpeg` 为其他包管理方案（仅在构建阶段使用其下载能力）
- 不自行编译 FFmpeg（使用预编译二进制）
- 不修改 FFmpeg 相关的 preset 逻辑
- 不实现 FFmpeg 在线更新机制
- 不涉及 Android 端 FFmpeg 支持（已搁置）

## Decisions

### Decision 1: 使用 static-ffmpeg 预下载 + PyInstaller 打包

**方案：** 构建时调用 `static_ffmpeg.add_paths()` 完成下载，然后从其缓存目录复制二进制到 `ffmpeg_binaries/`，最后通过 PyInstaller `binaries` 配置打包。

**替代方案：**
- 直接从 gyan.dev / johnvansickle 下载官方静态编译版 → 版本号难以与 static-ffmpeg 保持一致，增加维护负担
- 使用 `ffmpeg-python` 的 wheel 包 → 不提供二进制文件，只是一个 Python wrapper

**选择理由：**
- 复用 `static-ffmpeg` 已有的下载和平台检测逻辑，无需自行管理下载 URL
- 版本一致性有保障（同一个包负责下载和开发时使用）
- 代码改动最小，风险可控

### Decision 2: 运行时检测 frozen 环境以区分打包/开发

**方案：** 使用 `getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')` 检测 PyInstaller 打包环境。

**选择理由：**
- PyInstaller 标准检测方式，可靠且轻量
- 打包环境下优先从 `sys._MEIPASS` 附属目录查找 FFmpeg
- 开发环境回退到现有 `static_ffmpeg.add_paths()` + PATH 查找逻辑

## Risks / Trade-offs

- **[包体积增大 80-120MB]** → 可接受，FFmpeg 是核心功能依赖。可通过 UPX 压缩（已在 app.spec 中启用）缓解
- **[FFmpeg 版本需要手动更新]** → 构建脚本中添加版本检测逻辑，当 static-ffmpeg 更新时自动获取新版本
- **[macOS 代码签名/公证]** → FFmpeg 二进制可能触发 Gatekeeper 警告，需要在 onedir 模式下对 ffmpeg/ffprobe 单独签名（作为后续优化项）
- **[onefile 模式启动时间]** → FFmpeg 二进制增加解压时间，onedir 模式不受影响（推荐 onedir 分发）
