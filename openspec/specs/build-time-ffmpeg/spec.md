### Requirement: Build script downloads FFmpeg before packaging
构建脚本 `build.py` 在执行 PyInstaller 打包前，SHALL 自动调用预下载脚本获取当前平台的 FFmpeg (ffmpeg + ffprobe) 二进制文件到 `ffmpeg_binaries/` 目录。如果该目录已存在且包含有效的二进制文件，SHALL 跳过下载。

#### Scenario: First build on macOS
- **WHEN** 开发者在 macOS 上执行 `uv run build.py`
- **THEN** 系统下载 macOS 平台的 ffmpeg 和 ffprobe 到 `ffmpeg_binaries/` 目录，然后执行 PyInstaller 打包

#### Scenario: Build with existing binaries
- **WHEN** `ffmpeg_binaries/` 目录已存在且包含有效的 ffmpeg 二进制
- **THEN** 构建脚本跳过下载步骤，直接使用现有二进制进行打包

#### Scenario: Download failure
- **WHEN** 预下载过程中网络不可用或下载失败
- **THEN** 构建脚本 SHALL 报错退出，提示用户检查网络连接

### Requirement: PyInstaller bundles FFmpeg binaries
`app.spec` 和 `_generate_onefile_spec()` SHALL 将 `ffmpeg_binaries/` 中的 ffmpeg 和 ffprobe 作为 binaries 打包进最终产物。

#### Scenario: onedir build includes FFmpeg
- **WHEN** 执行 `uv run build.py` (onedir 模式)
- **THEN** `dist/app/` 目录中包含 ffmpeg 和 ffprobe 可执行文件

#### Scenario: onefile build includes FFmpeg
- **WHEN** 执行 `uv run build.py --onefile`
- **THEN** 生成的可执行文件包含 FFmpeg 二进制，运行时解压后可用

### Requirement: Packaged app uses bundled FFmpeg
在 PyInstaller 打包环境下，`core/ffmpeg_setup.py` SHALL 优先从打包目录（`sys._MEIPASS`）查找 FFmpeg 二进制，SHALL NOT 调用 `static_ffmpeg.add_paths()` 进行运行时下载。

#### Scenario: Packaged app finds bundled FFmpeg
- **WHEN** 打包后的应用启动，调用 `ensure_ffmpeg()`
- **THEN** 系统从 `sys._MEIPASS` 关联目录找到 ffmpeg 二进制，不触发网络下载

#### Scenario: Bundled FFmpeg not found
- **WHEN** 打包后的应用启动但 FFmpeg 二进制意外缺失
- **THEN** `ensure_ffmpeg()` 返回 False，应用 SHALL 向用户展示明确的错误提示

### Requirement: Dev environment preserves current behavior
在非打包环境下，`core/ffmpeg_setup.py` SHALL 保持现有逻辑：优先查找系统 PATH 中的 ffmpeg，未找到则使用 `static_ffmpeg.add_paths()` 下载。

#### Scenario: Dev with system FFmpeg
- **WHEN** 开发者系统 PATH 中已安装 ffmpeg
- **THEN** `get_ffmpeg_path()` 返回系统 ffmpeg 路径，不触发 static-ffmpeg 下载

#### Scenario: Dev without system FFmpeg
- **WHEN** 开发者系统未安装 ffmpeg
- **THEN** `ensure_ffmpeg()` 调用 `static_ffmpeg.add_paths()` 下载并返回下载后的路径
