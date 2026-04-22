# Android FFmpeg 支持方案（搁置）

> **状态：** 搁置
> **搁置日期：** 2026-03-30
> **搁置原因：** 优先完成 Desktop 端 FFmpeg 打包改进，Android 端复杂度较高，后续单独推进
> **来源：** `openspec/changes/ffmpeg-packaging-improvement` 的 Android 相关 artifacts

---

## 问题背景

`static-ffmpeg` 不支持 Android 平台，Android 端无法通过运行时下载获取 FFmpeg。需要单独的 ARM64 FFmpeg 方案。

## 技术方案探索

### 方案 A：预编译 ARM64 二进制打包到 assets（推荐）

从 FFmpeg 官方或社区获取 ARM64 预编译二进制，放入 `ffmpeg_binaries/android-arm64/`，通过 buildozer 打包，运行时复制到应用私有目录执行。

**优点：** 纯 Python 实现，与 Desktop 端 subprocess 调用方式一致
**缺点：** 需要维护 ARM64 二进制的来源和更新

### 方案 B：ffmpeg-kit (Gradle 依赖)

使用 `com.arthenica:ffmpeg-kit:6.0-2` Gradle 依赖提供 FFmpeg。

**优点：** 功能完整，官方维护
**缺点：** 需要 JNI 桥接和 Java/Kotlin 代码，复杂度极高

### 方案 C：Termux FFmpeg

检测 Termux 环境，使用 `pkg install ffmpeg`。

**优点：** 最简单
**缺点：** 仅限技术用户，不适合普通用户

## 已规划的实现内容（搁置前状态）

### 代码文件

- `core/ffmpeg_android.py` — Android 平台 FFmpeg 路径管理器
  - `is_android()`: 检测 `ANDROID_ROOT` / `ANDROID_DATA` 环境变量
  - `setup_ffmpeg_android()`: 从 assets 复制 FFmpeg 到应用私有目录

### 构建修改

- `build.py` 的 `_build_android()`: 构建前下载 ARM64 FFmpeg
- `build.py` 的 `_generate_buildozer_spec()`: 添加存储权限
- `buildozer.spec`: 添加 `WRITE_EXTERNAL_STORAGE`、`READ_EXTERNAL_STORAGE` 权限

### 二进制来源

- [johnvansickle/ffmpeg](https://github.com/johnvansickle/ffmpeg) 的 Android ARM64 release
- [tanersener/mobile-ffmpeg](https://github.com/tanersener/mobile-ffmpeg/releases)
- [arthenica/ffmpeg-kit](https://github.com/arthenica/ffmpeg-kit) 的 ARM 版本

### 风险

- ARM64 二进制在不同设备上的兼容性
- Android 存储权限限制（Scoped Storage on API 30+）
- assets 中二进制的执行权限问题

---

## 恢复此需求时的检查清单

- [ ] 确认 Desktop 端 FFmpeg 打包方案已稳定
- [ ] 评估 Android 端是否仍使用 Buildozer（可能有其他打包方案）
- [ ] 确认 ARM64 二进制来源可用
- [ ] 在 Android 模拟器/真机上验证 FFmpeg 执行
- [ ] 处理 Android Scoped Storage 限制（API 30+）
