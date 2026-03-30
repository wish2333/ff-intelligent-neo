## 1. Desktop 预下载脚本

- [x] 1.1 创建 `scripts/` 目录和 `scripts/pre_build.py`：实现 `download_ffmpeg()` 函数，调用 `static_ffmpeg.add_paths()` 下载当前平台 FFmpeg，从缓存目录复制 ffmpeg/ffprobe 到项目 `ffmpeg_binaries/` 目录
- [x] 1.2 在 `pre_build.py` 中添加跳过逻辑：如果 `ffmpeg_binaries/` 已包含有效的 ffmpeg 二进制（可用 `subprocess.run(["ffmpeg_binaries/ffmpeg", "-version"])` 验证），跳过下载
- [x] 1.3 在 `pre_build.py` 中添加错误处理：下载失败时报错退出，给出网络检查提示

## 2. Desktop 构建流程集成

- [x] 2.1 修改 `build.py` 的 `_build_onedir()`：在 PyInstaller 执行前调用 `scripts/pre_build.py` 预下载 FFmpeg
- [x] 2.2 修改 `build.py` 的 `_build_onefile()`：在 spec 生成和 PyInstaller 执行前调用 `scripts/pre_build.py` 预下载 FFmpeg
- [x] 2.3 修改 `app.spec`：在 `binaries` 列表中添加 `ffmpeg_binaries/ffmpeg` 和 `ffmpeg_binaries/ffprobe`（Windows 需加 `.exe` 后缀）
- [x] 2.4 修改 `build.py` 的 `_generate_onefile_spec()`：在生成的 spec 中同样添加 FFmpeg binaries 配置

## 3. 运行时 FFmpeg 路径逻辑

- [x] 3.1 在 `core/ffmpeg_setup.py` 中添加 `is_frozen()` 函数：使用 `getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')` 检测打包环境
- [x] 3.2 修改 `_find_static_ffmpeg_bin()`：在打包环境下优先从 `sys._MEIPASS` 查找 ffmpeg/ffprobe 二进制
- [x] 3.3 修改 `ensure_ffmpeg()`：打包环境下跳过 `static_ffmpeg.add_paths()` 调用，开发环境保持不变

## 4. 验证与清理

- [x] 4.1 在 macOS 上测试 onedir 构建：验证 `dist/app/` 中包含 ffmpeg/ffprobe 且应用可正常调用
- [x] 4.2 在 macOS 上测试 onefile 构建：验证单文件应用可正常使用 FFmpeg
- [x] 4.3 验证开发环境未受影响：删除 `ffmpeg_binaries/` 后 `uv run main.py` 仍能通过 static-ffmpeg 下载并使用 FFmpeg
- [x] 4.4 将 `ffmpeg_binaries/` 添加到 `.gitignore`（下载产物不入库）
