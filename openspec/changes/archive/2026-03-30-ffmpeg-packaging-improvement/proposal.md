## Why

`static-ffmpeg` 在**运行时**下载 FFmpeg 二进制文件，导致用户首次启动必须联网且等待时间不可控，打包后的应用体验不可靠。需要在构建阶段预获取 FFmpeg 并将其打包进最终产物，实现用户开箱即用。

> **注意：** Android 端 FFmpeg 支持方案已搁置，相关探索和计划归档于 `docs/shelved/android-ffmpeg-support.md`。

## What Changes

- 新增构建前脚本 `scripts/pre_build.py`：在 `uv run build.py` 执行时自动下载当前平台的 FFmpeg 二进制到 `ffmpeg_binaries/` 目录
- 修改 `app.spec` 和 `_generate_onefile_spec()`：将预下载的 ffmpeg/ffprobe 加入 PyInstaller `binaries`
- 修改 `core/ffmpeg_setup.py`：打包环境下优先从打包目录查找 FFmpeg，跳过 `static_ffmpeg.add_paths()` 的运行时下载；开发环境保持现有行为不变
- 修改 `build.py`：在 `_build_onedir()` 和 `_build_onefile()` 前自动调用预下载脚本

## Capabilities

### New Capabilities
- `build-time-ffmpeg`: 构建阶段预下载并打包 FFmpeg 二进制文件到应用产物中

### Modified Capabilities
（无现有 spec 需要修改）

## Impact

### 代码影响
- `build.py` — 添加预下载调用步骤
- `app.spec` — 添加 binaries 配置
- `core/ffmpeg_setup.py` — 区分打包环境/开发环境的 FFmpeg 查找逻辑
- 新增文件：`scripts/pre_build.py`

### 依赖影响
- `static-ffmpeg` 保留为 dev 依赖（开发环境使用），生产包中不再运行时依赖其下载功能

### 构建产物影响
- Desktop 包体积增加约 80-120MB（FFmpeg 静态二进制）
- 构建时间略微增加（需下载/复制 FFmpeg）

### 风险
- FFmpeg 版本需要与 static-ffmpeg 发布的版本保持一致或单独维护
