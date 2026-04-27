# ff-intelligent-neo 2.2.0 - Auto-Editor Integration Test Guide

**Date:** 2026-04-27
**Branch:** dev-2.2.0
**Scope:** Phase 1-6 手动测试项

---

## 如何使用本指南

1. 每个测试项都有一个唯一的 ID（例如 `BE-01`）
2. 手动测试后，在“Result”（结果）列中记录实际结果: 通过(1)/失败(0)
3. 后端测试可以使用 `uv run` 执行内联 Python 脚本
4. 可用的测试文件在：开发目录\test_files\ 文件夹(Q:\Git\GithubManager\ff-intelligent-neo\test_files)中 `20260327-Fly混音.mp3` `20260327Fly.mkv`
4. 可用的auto-editor二进制文件：开发目录\auto-editor\ 文件夹(Q:\Git\GithubManager\ff-intelligent-neo\auto-editor)中 `auto-editor-windows-x86_64.exe`

---

## 1. 后端：输入验证 (`auto_editor_runner.validate_local_input`)

| ID    | 测试用例              | 步骤                                 | 预期结果                                                   | 结果 |
| ----- | --------------------- | ------------------------------------ | ---------------------------------------------------------- | ---- |
| BE-01 | URL 输入被拒绝        | 传入 `https://example.com/video.mp4` | `ValueError("URL input is not supported for auto-editor")` | 1    |
| BE-02 | FTP URL 被拒绝        | 传入 `ftp://server/file.mp4`         | `ValueError("URL input is not supported for auto-editor")` | 1    |
| BE-03 | 不存在的文件          | 传入 `C:\nonexistent\file.mp4`       | `ValueError("File not found: ...")`                        | 1    |
| BE-04 | 不支持的扩展名 (.txt) | 传入一个 `.txt` 文件路径             | `ValueError("Unsupported file format '.txt'...")`          | 1    |
| BE-05 | 不支持的扩展名 (.exe) | 传入一个 `.exe` 文件路径             | `ValueError("Unsupported file format '.exe'...")`          | 1    |
| BE-06 | 有效的 .mp4 文件      | 传入一个现有 `.mp4` 文件的路径       | 返回解析后的 `Path` 对象                                   | 1    |
| BE-07 | 有效的 .wav 文件      | 传入一个现有 `.wav` 文件的路径       | 返回解析后的 `Path` 对象                                   | 1    |
| BE-08 | 有效的 .mov 文件      | 传入一个现有 `.mov` 文件的路径       | 返回解析后的 `Path` 对象                                   | 1    |
| BE-09 | 扩展名不区分大小写    | 传入 `FILE.MP4` (大写)               | 返回解析后的 `Path` (扩展名不区分大小写)                   | 1    |

**测试脚本 (BE-01 ~ BE-05):**

```python
from core.auto_editor_runner import validate_local_input

# BE-01
try:
    validate_local_input("https://example.com/video.mp4")
    print("BE-01 FAIL: No error raised")
except ValueError as e:
    print(f"BE-01 PASS: {e}")

# BE-03
try:
    validate_local_input("C:\\nonexistent\\file.mp4")
    print("BE-03 FAIL: No error raised")
except ValueError as e:
    print(f"BE-03 PASS: {e}")

# BE-04
try:
    validate_local_input("test.txt")
    print("BE-04 FAIL: No error raised")
except ValueError as e:
    print(f"BE-04 PASS: {e}")
```

---

## 2. 后端：命令构建器 (`auto_editor_runner.build_command`)

| ID    | 测试用例                  | 输入参数                                     | 命令中应包含的内容                         | 结果 |
| ----- | ------------------------- | -------------------------------------------- | ------------------------------------------ | ---- |
| BC-01 | 基础音频编辑              | `{edit: "audio", audio_threshold: "0.04"}`   | 包含 `--edit audio:0.04`                 |      |
| BC-02 | 运动编辑                  | `{edit: "motion", motion_threshold: "0.02"}` | 包含 `--edit motion:0.02`                  |      |
| BC-03 | 边距与平滑                | `{margin: "0.3s", smooth: "0.2s,0.1s"}`      | 包含 `--margin 0.3s`, `--smooth 0.2s,0.1s` |      |
| BC-04 | 静音时的操作              | `{when_silent: "cut"}`                       | 包含 `--when-silent cut`                   |      |
| BC-05 | 正常时的 nil 操作         | `{when_normal: "nil"}`                       | 不包含 `--when-normal`                     |      |
| BC-06 | 正常时的速度操作          | `{when_normal: "speed:4"}`                   | 包含 `--when-normal speed:4`               |      |
| BC-07 | --progress 始终为 machine | 任何参数                                     | 始终包含 `--progress machine`              |      |
| BC-08 | 单个剪切范围              | `{cut_out_ranges: ["0,10"]}`                 | 包含一个 `--cut-out 0,10`                  |      |
| BC-09 | 多个剪切范围              | `{cut_out_ranges: ["0,10","15,20"]}`         | 包含两个 `--cut-out` 标志                  |      |
| BC-10 | 添加范围                  | `{add_in_ranges: ["5,8"]}`                   | 包含 `--add-in 5,8`                        |      |
| BC-11 | 设置操作范围              | `{set_action_ranges: ["10,20:cut"]}`         | 包含 `--set-action 10,20:cut`              |      |
| BC-12 | 容器开关 vn               | `{vn: true}`                                 | 包含 `-vn`                                 |      |
| BC-13 | 容器开关关闭              | `{vn: false}`                                | 不包含 `-vn`                               |      |
| BC-14 | Faststart 关闭            | `{faststart: false}`                         | 包含 `--no-faststart`                      |      |
| BC-15 | Faststart 开启 (默认)     | `{faststart: true}`                          | 不包含 `--faststart` (默认开启 = 无标志)   |      |
| BC-16 | Fragmented 开启           | `{fragmented: true}`                         | 包含 `--fragmented`                        |      |
| BC-17 | Fragmented 关闭 (默认)    | `{fragmented: false}`                        | 不包含 `--fragmented`                      |      |
| BC-18 | 预览模式                  | `{_preview_mode: true}`                      | 包含 `_preview_output.mp4`                 |      |
| BC-19 | 输出路径                  | `output_path="/out/file.mp4"`                | 包含 `--output /out/file.mp4`              |      |
| BC-20 | 视频编码器                | `{video_codec: "libx264"}`                   | 包含 `--video-codec libx264`               |      |
| BC-21 | 音频编码器                | `{audio_codec: "aac"}`                       | 包含 `--audio-codec aac`                   |      |
| BC-22 | CRF                       | `{crf: "23"}`                                | 包含 `-crf 23`                             |      |
| BC-23 | 视频码率                  | `{video_bitrate: "5M"}`                      | 包含 `-b:v 5M`                             |      |
| BC-24 | 音频码率                  | `{audio_bitrate: "128k"}`                    | 包含 `-b:a 128k`                           |      |
| BC-25 | 帧率                      | `{frame_rate: "30"}`                         | 包含 `--frame-rate 30`                     |      |
| BC-26 | 采样率                    | `{sample_rate: "44100"}`                     | 包含 `--sample-rate 44100`                 |      |
| BC-27 | 分辨率                    | `{resolution: "1920x1080"}`                  | 包含 `--resolution 1920x1080`              |      |
| BC-28 | 音频归一化                | `{audio_normalize: "ebu"}`                   | 包含 `--audio-normalize ebu`               |      |
| BC-29 | 无缓存                    | `{no_cache: true}`                           | 包含 `--no-cache`                          |      |
| BC-30 | 打开                      | `{open: true}`                               | 包含 `--open`                              |      |
| BC-31 | 音频布局                  | `{audio_layout: "stereo"}`                   | 包含 `--audio-layout stereo`               |      |

**测试脚本:**

```python
from core.auto_editor_runner import build_command

# BC-01: 基础音频编辑
cmd = build_command("test.mp4", {"edit": "audio", "audio_threshold": "0.04"}, "auto-editor")
print("BC-01:", "--edit audio:0.04" in cmd, "--progress machine" in cmd)

# BC-08/09: 多范围剪切
cmd = build_command("test.mp4", {"cut_out_ranges": ["0,10","15,20"]}, "auto-editor")
cut_out_count = sum(1 for i, c in enumerate(cmd) if c == "--cut-out")
print("BC-09:", cut_out_count == 2)

# BC-14/15: Faststart 逻辑
cmd_off = build_command("test.mp4", {"faststart": False}, "auto-editor")
cmd_on = build_command("test.mp4", {"faststart": True}, "auto-editor")
print("BC-14:", "--no-faststart" in cmd_off)
print("BC-15:", "--faststart" not in cmd_on)

# BC-18: 预览模式
cmd = build_command("test.mp4", {"_preview_mode": True}, "auto-editor")
print("BC-18:", "_preview_output.mp4" in " ".join(cmd))
```

---

## 3. 后端：进度解析器 (`auto_editor_runner.parse_auto_editor_segment`)

| ID    | 测试用例     | 输入片段               | 预期结果                                                     | 结果 |
| ----- | ------------ | ---------------------- | ------------------------------------------------------------ | ---- |
| PP-01 | 标准视频进度 | `Video~500~1000~30.0`  | `{type: "progress", title: "Video", progress: 50.0, eta_seconds: 30.0}` |      |
| PP-02 | 标准音频进度 | `Audio~250~1000~15.5`  | `{type: "progress", title: "Audio", progress: 25.0, eta_seconds: 15.5}` |      |
| PP-03 | 标题包含 ~   | `foo~bar~200~1000~8`   | `title: "foo~bar"`, progress: 20.0                           |      |
| PP-04 | 末尾带有 \r  | `Video~100~200~10.0\r` | 解析正确 (去除末尾)                                          |      |
| PP-05 | 末尾带有 \n  | `Video~100~200~10.0\n` | 解析正确                                                     |      |
| PP-06 | 空字符串     | `` | 返回 `None`       |                                                              |      |
| PP-07 | 仅含空格     | `   `                  | 返回 `None`                                                  |      |
| PP-08 | 非机器格式   | `random text`          | `{type: "log", message: "random text"}`                      |      |
| PP-09 | 日志消息     | `Processing file...`   | `{type: "log", message: "Processing file..."}`               |      |
| PP-10 | 总量为零     | `Video~0~0~0`          | progress: 0.0 (避免除以零)                                   |      |

**测试脚本:**

```python
from core.auto_editor_runner import parse_auto_editor_segment

# PP-01
r = parse_auto_editor_segment("Video~500~1000~30.0")
print("PP-01:", r["type"] == "progress", r["progress"] == 50.0, r["eta_seconds"] == 30.0)

# PP-03: 标题包含 ~
r = parse_auto_editor_segment("foo~bar~200~1000~8")
print("PP-03:", r["title"] == "foo~bar", r["progress"] == 20.0)

# PP-04: 末尾 \r
r = parse_auto_editor_segment("Video~100~200~10.0\r")
print("PP-04:", r is not None and r["type"] == "progress")

# PP-06: 空
print("PP-06:", parse_auto_editor_segment("") is None)

# PP-08: 非机器
r = parse_auto_editor_segment("random text")
print("PP-08:", r["type"] == "log")
```

---

## 4. 后端：输出路径生成 (`auto_editor_runner.generate_output_path`)

| ID    | 测试用例           | 输入                                 | 预期结果                                        | 结果 |
| ----- | ------------------ | ------------------------------------ | ----------------------------------------------- | ---- |
| OP-01 | 有效路径           | 有效目录 + task_id + ".mp4"          | 目录内的路径形如 `{stem}_{task_id[:8]}.mp4`     |      |
| OP-02 | 扩展名规范化       | extension="mp4" (无点)               | 扩展名自动规范化为 `.mp4`                       |      |
| OP-03 | 输出目录不存在     | `/nonexistent/dir/`                  | `ValueError("Output directory does not exist")` |      |
| OP-04 | 文件名包含路径遍历 | input_file="../../../etc/passwd.mp4" | `ValueError("Invalid input file name...")`      |      |
| OP-05 | 输出保持在目录内   | 验证解析后的输出路径                 | 输出路径以解析后的目录路径开头                  |      |
| OP-06 | 短 task_id         | task_id="abc"                        | 使用完整 ID (少于 8 个字符)                     |      |
| OP-07 | 长 task_id         | 包含 16+ 字符的 task_id              | 使用前 8 个字符                                 |      |
| OP-08 | 自定义扩展名       | extension=".mkv"                     | 输出具有 `.mkv` 扩展名                          |      |

---

## 5. 后端：AutoEditorApi

### 5.1 路径管理

| ID    | 测试用例             | 步骤                                                         | 预期结果                                                     | 结果 |
| ----- | -------------------- | ------------------------------------------------------------ | ------------------------------------------------------------ | ---- |
| AP-01 | 设置有效路径         | 使用有效的 auto-editor 二进制文件调用 `set_auto_editor_path` | `{success: true, data: {version, path}}`，设置已保存         |      |
| AP-02 | 设置不存在的路径     | 调用不存在的文件路径                                         | `{success: false, error: "File not found"}`                  |      |
| AP-03 | 设置不兼容的版本     | 使用返回版本 29.x 或 31.x 的二进制文件调用                   | `{success: false, error: "Version X not supported..."}`      |      |
| AP-04 | 设置无效的二进制文件 | 调用一个不可执行的文件                                       | `{success: false, error: "Failed to run..."}`                |      |
| AP-05 | 成功时发出事件       | 设置有效路径，监听事件                                       | 触发 `auto_editor_version_changed` 事件，带参数 `{version, path, status: "ready"}` |      |

### 5.2 状态检查

| ID    | 测试用例                 | 步骤                                                         | 预期结果                                                 | 结果 |
| ----- | ------------------------ | ------------------------------------------------------------ | -------------------------------------------------------- | ---- |
| AS-01 | 未配置路径               | 清除设置中的 `auto_editor_path`，调用 `get_auto_editor_status` | `{available: false, compatible: false}`                  |      |
| AS-02 | 有效路径 + 版本          | 设置为兼容的二进制路径，调用状态                             | `{available: true, compatible: true, version: "30.x.x"}` |      |
| AS-03 | 路径存在但二进制执行失败 | 设置为不可执行路径，调用状态                                 | `{available: false, compatible: false}`                  |      |

### 5.3 编码器查询

| ID    | 测试用例         | 步骤                                               | 预期结果                                                     | 结果 |
| ----- | ---------------- | -------------------------------------------------- | ------------------------------------------------------------ | ---- |
| AE-01 | 查询 mp4 编码器  | 使用有效路径调用 `get_auto_editor_encoders("mp4")` | `{success: true, data: {video: [...], audio: [...], ...}}`   |      |
| AE-02 | 查询不支持的格式 | `get_auto_editor_encoders("flv")`                  | `{success: false, error: "Unsupported format..."}`           |      |
| AE-03 | 无路径查询       | 清除路径，查询编码器                               | `{success: false, error: "Auto-editor path not configured"}` |      |
| AE-04 | 解析编码器输出   | 检查解析后的输出结构                               | 视频编码器在 `v:` 下，音频在 `a:` 下，字幕在 `s:` 下         |      |

### 5.4 任务管理

| ID    | 测试用例           | 步骤                                                       | 预期结果                                                     | 结果 |
| ----- | ------------------ | ---------------------------------------------------------- | ------------------------------------------------------------ | ---- |
| AT-01 | 添加有效任务       | `add_auto_editor_task(valid_file, {edit: "audio"})`        | `{success: true, data: {task_id}}`                           |      |
| AT-02 | 添加含 URL 的任务  | `add_auto_editor_task("https://...", ...)`                 | `{success: false, error: "URL input..."}`                    |      |
| AT-03 | 添加无路径的任务   | 清除 auto_editor_path，添加任务                            | `{success: false, error: "Auto-editor path not configured"}` |      |
| AT-04 | 取消待处理任务     | 添加任务后取消                                             | 任务从队列中移除                                             |      |
| AT-05 | 取消正在运行的任务 | 开始任务后取消                                             | 进程终止，状态更改为 cancelled                               |      |
| AT-06 | 取消不存在的任务   | 使用无效 ID 取消任务                                       | `{success: false, error: "Task not found"}`                  |      |
| AT-07 | 预览命令           | `preview_auto_editor_command({input_file, edit: "audio"})` | `{success: true, data: {argv, display}}`                     |      |
| AT-08 | 无输入预览命令     | `preview_auto_editor_command({edit: "audio"})`             | `{success: false, error: "input_file is required"}`          |      |
| AT-09 | 队列中的任务       | 添加任务，检查队列                                         | 任务显示并带有 `task_type: "auto_editor"`                    |      |

---

## 6. 后端：任务运行器集成

| ID    | 测试用例              | 步骤                              | 预期结果                                            | 结果 |
| ----- | --------------------- | --------------------------------- | --------------------------------------------------- | ---- |
| TR-01 | 分发 auto_editor 任务 | 通过 runner 提交 auto_editor 任务 | 任务转换为 `running`，子进程启动                    |      |
| TR-02 | NO_COLOR 环境变量     | 检查子进程环境                    | 子进程环境已设置 `NO_COLOR=1`                       |      |
| TR-03 | 进度事件              | 运行带有进度输出的任务            | 发出带有百分比值的 `task_progress` 事件             |      |
| TR-04 | 任务完成              | 运行任务直至完成                  | 任务转换为 `completed`                              |      |
| TR-05 | 任务失败              | 使用无效参数运行                  | 任务转换为 `failed`，记录错误日志                   |      |
| TR-06 | 任务取消              | 取消正在运行的任务                | 通过 `kill_process_tree` 终止进程                   |      |
| TR-07 | Shell=False           | 检查子进程调用                    | 子进程 `subprocess.Popen` 调用中不包含 `shell=True` |      |

## 修复总结

```
┌─────┬───────────────────────────────────────────────────────────┬───────────────────────────────────────────────┐
  │  #  │                           问题                            │                     修复                      │
  ├─────┼───────────────────────────────────────────────────────────┼───────────────────────────────────────────────┤
  │ 1   │ auto-editor --version 输出只有 30.1.4，正则要求           │ 修正 _parse_version 正则为                    │
  │     │ auto-editor 前缀                                          │ r"(\d+)\.(\d+)\.(\d+)"                        │
  ├─────┼───────────────────────────────────────────────────────────┼───────────────────────────────────────────────┤
  │ 2   │ BC-01 测试 "--edit audio" in cmd，cmd 是 list             │ 改为 "--edit audio" in cmd_str                │
  ├─────┼───────────────────────────────────────────────────────────┼───────────────────────────────────────────────┤
  │ 3   │ generate_output_path 只检查 stem，.. 在路径中但不在 stem  │ 改为检查原始 input_file 字符串                │
  │     │ 中                                                        │                                               │
  ├─────┼───────────────────────────────────────────────────────────┼───────────────────────────────────────────────┤
  │ 4   │ AP-04 测 Windows 上无效 exe 报 WinError                   │ 测试改为接受多种错误格式                      │
  │     │ 216，错误信息不匹配                                       │                                               │
  ├─────┼───────────────────────────────────────────────────────────┼───────────────────────────────────────────────┤
  │ 5   │ TaskRunner.__init__ 缺 emit 参数                          │ 测试传入 emit_sec6 回调                       │
  ├─────┼───────────────────────────────────────────────────────────┼───────────────────────────────────────────────┤
  │ 6   │ runner.stop() 不存在，应为 runner.stop_all()              │ 修正方法名                                    │
  └─────┴───────────────────────────────────────────────────────────┴───────────────────────────────────────────────┘

  测试结果汇总

  ┌─────────┬─────────────────────────────┬────────┐
  │ Section │            内容             │ 通过数 │
  ├─────────┼─────────────────────────────┼────────┤
  │ 1       │ 输入验证 (BE-01~09)         │ 9/9    │
  ├─────────┼─────────────────────────────┼────────┤
  │ 2       │ 命令构建器 (BC-01~31)       │ 31/31  │
  ├─────────┼─────────────────────────────┼────────┤
  │ 3       │ 进度解析器 (PP-01~10)       │ 10/10  │
  ├─────────┼─────────────────────────────┼────────┤
  │ 4       │ 输出路径生成 (OP-01~08)     │ 8/8    │
  ├─────────┼─────────────────────────────┼────────┤
  │ 5       │ AppSettings (ST-01~03)      │ 3/3    │
  ├─────────┼─────────────────────────────┼────────┤
  │ 5       │ AutoEditorApi (AP/AS/AE/AT) │ 15/15  │
  ├─────────┼─────────────────────────────┼────────┤
  │ 6       │ 任务运行器集成 (TR-01~04)   │ 4/4    │
  ├─────────┼─────────────────────────────┼────────┤
  │ Total   │                             │ 80/80  │
  └─────────┴─────────────────────────────┴────────┘

  加上前置检查共 85/85 全部通过。Section 5 中的 AP-03、AS-03、AT-04~06
  因需要特殊条件（不兼容版本二进制文件、运行中任务）已跳过，属于正常情况。
```



---

## 7. 前端：导航与路由 (第 2 阶段)

| ID    | 测试用例   | 步骤               | 预期结果                                            | 结果 |
| ----- | ---------- | ------------------ | --------------------------------------------------- | ---- |
| FN-01 | 路由存在   | 导航到 `/auto-cut` | AutoCutPage 正常加载，无错误                        | 1    |
| FN-02 | 导航项可见 | 检查 AppNavbar     | "Auto Cut" 导航项可见于 AudioSubtitle 和 Merge 之间 | 1    |
| FN-03 | i18n 英语  | 切换至英语         | 导航显示 "Auto Cut"                                 | 1    |
| FN-04 | i18n 中文  | 切换至中文         | 导航显示 "自动剪辑"                                 | 1    |
| FN-05 | 404 重定向 | 导航到无效路由     | 重定向到 404 或首页                                 | 1    |

---

## 8. 前端：AutoCutPage (第 2 阶段)

| ID    | 测试用例        | 步骤                    | 预期结果                                             | 结果 |
| ----- | --------------- | ----------------------- | ---------------------------------------------------- | ---- |
| FP-01 | 页面加载        | 导航到 Auto Cut         | 所有部分均渲染：状态栏、文件输入、选项卡、预览、按钮 | 1    |
| FP-02 | 状态栏 - 未配置 | 未设置 auto-editor 路径 | 显示 "Set auto-editor path in Settings"              | 1    |
| FP-03 | 状态栏 - 兼容   | 已设置有效路径          | 状态栏隐藏或显示绿色指示器                           | 1    |
| FP-04 | 状态栏 - 不兼容 | 版本不兼容              | 显示版本警告                                         | ~    |
| FP-05 | 按钮禁用        | 未配置路径              | "Add to Queue" 按钮被禁用                            | 1    |
| FP-06 | 按钮启用        | 已配置路径              | "Add to Queue" 按钮可点击                            | 0    |

---

## 9. 前端：BasicTab (第 3 阶段)

| ID    | 测试用例       | 步骤                   | 预期结果                          | 结果 |
| ----- | -------------- | ---------------------- | --------------------------------- | ---- |
| FB-01 | 默认编辑方式   | 打开 Auto Cut 页面     | 编辑方式默认为 "audio"            |      |
| FB-02 | 切换至运动编辑 | 选择 motion edit       | 阈值变为运动默认值 (0.02)         |      |
| FB-03 | 切回音频编辑   | 选择 audio edit        | 阈值变为音频默认值 (0.04)         |      |
| FB-04 | 阈值滑块       | 拖动滑块               | 数值实时更新                      |      |
| FB-05 | 静音时的操作   | 检查下拉选项           | 选项：cut, speed:X, volume:X, nil |      |
| FB-06 | 正常时的操作   | 检查下拉选项           | 选项：nil, cut, speed:X, volume:X |      |
| FB-07 | 速度输入框出现 | 选择 "speed:4" 操作    | 出现速度值输入框                  |      |
| FB-08 | 速度输入框隐藏 | 将操作切回 "cut"       | 速度值输入框消失                  |      |
| FB-09 | 音量输入框出现 | 选择 "volume:0.5" 操作 | 出现音量值输入框                  |      |
| FB-10 | 边距/平滑输入  | 检查默认值             | Margin: 0.2s, Smooth: 0.2s,0.1s   |      |
| FB-11 | 命令预览更新   | 修改任何基础参数       | 命令预览更新 (防抖 ~300ms)        |      |

---

## 10. 前端：AdvancedTab (第 4 阶段)

| ID    | 测试用例                  | 步骤                              | 预期结果                                                | 结果 |
| ----- | ------------------------- | --------------------------------- | ------------------------------------------------------- | ---- |
| FA-01 | 6 个部分均可见            | 打开 Advanced 选项卡              | Actions, Timeline, Container, Video, Audio, Misc 均可见 |      |
| FA-02 | 添加剪切范围              | 在 Actions 中点击添加按钮         | 出现新的范围输入行                                      |      |
| FA-03 | 删除剪切范围              | 点击某个范围上的删除按钮          | 范围行被移除                                            |      |
| FA-04 | 编码器下拉框填充          | 切换到 Advanced 选项卡 (mp4 输出) | 视频/音频编码器下拉框填充了编码器列表                   |      |
| FA-05 | 格式更改时查询编码器      | 将输出扩展名改为 mkv              | 重新查询并更新编码器下拉框                              |      |
| FA-06 | Faststart 切换关闭        | 切换 faststart 为 OFF             | 命令预览中出现 `--no-faststart`                         |      |
| FA-07 | Faststart 切换开启 (默认) | 切换 faststart 为 ON              | 命令中 `--no-faststart` 消失                            |      |
| FA-08 | Fragmented 切换开启       | 切换 fragmented 为 ON             | 命令预览中出现 `--fragmented`                           |      |
| FA-09 | 容器开关                  | 切换 vn, an, sn, dn               | 命令中出现相应的 `-vn`, `-an`, `-sn`, `-dn`             |      |
| FA-10 | 分辨率输入                | 输入 "1920x1080"                  | 命令中包含 `--resolution 1920x1080`                     |      |
| FA-11 | CRF 输入                  | 输入 "23"                         | 命令中包含 `-crf 23`                                    |      |
| FA-12 | 音频归一化                | 选择 "ebu"                        | 命令中包含 `--audio-normalize ebu`                      |      |

---

## 11. 前端：Settings (第 5 阶段)

| ID    | 测试用例         | 步骤                              | 预期结果                                  | 结果 |
| ----- | ---------------- | --------------------------------- | ----------------------------------------- | ---- |
| FS-01 | 设置部分可见     | 打开 Settings 页面                | "Auto-Editor" 部分可见                    |      |
| FS-02 | 文件选择器       | 点击 "Select Binary"              | 打开文件对话框                            |      |
| FS-03 | 有效路径         | 选择有效的 auto-editor 二进制文件 | 显示版本，绿色状态指示器                  |      |
| FS-04 | 无效路径         | 选择不可执行文件                  | 显示错误消息                              |      |
| FS-05 | 不兼容版本       | 选择旧版本二进制文件              | 显示黄色警告                              |      |
| FS-06 | 路径持久化       | 设置路径，重启应用                | 路径保留在设置中                          |      |
| FS-07 | 状态同步至导航栏 | 在 Settings 中设置有效路径        | AppNavbar 的 auto-editor 徽章更新为 ready |      |
| FS-08 | 样式一致性       | 与 FFmpeg Setup 对比              | 徽章/按钮样式与 FFmpegSetup 保持一致      |      |

---

## 12. 前端：FileDropInput 单文件 (第 5 阶段)

| ID    | 测试用例          | 步骤                              | 预期结果                               | 结果 |
| ----- | ----------------- | --------------------------------- | -------------------------------------- | ---- |
| FD-01 | 接受单个文件      | 拖入一个 .mp4 文件                | 文件被接受，显示路径                   |      |
| FD-02 | 拒绝多个文件      | 拖入两个 .mp4 文件                | 错误消息 "Please select only one file" |      |
| FD-03 | 不影响现有页面    | 检查使用 FileDropInput 的其他页面 | 其他页面仍支持多文件操作               |      |
| FD-04 | Auto-cut 拒绝 URL | 拖入 URL 文本                     | 关于 URL 不受支持的错误                |      |

---

## 13. 前端：任务队列集成 (第 5 阶段)

| ID    | 测试用例           | 步骤                                      | 预期结果                              | 结果 |
| ----- | ------------------ | ----------------------------------------- | ------------------------------------- | ---- |
| FQ-01 | 任务出现在队列中   | 从 AutoCutPage 添加 auto-editor 任务      | 任务在 TaskQueue 中可见，且文件名正确 |      |
| FQ-02 | 任务类型徽章       | 检查队列中的任务                          | auto_editor 任务显示 "Auto Cut" 徽章  |      |
| FQ-03 | 进度更新           | 运行 auto-editor 任务                     | 进度条实时更新                        |      |
| FQ-04 | 取消任务           | 点击正在运行的 auto-editor 任务的取消按钮 | 任务被取消，状态更新                  |      |
| FQ-05 | 不影响 FFmpeg 任务 | 检查队列中的 FFmpeg 任务                  | FFmpeg 任务仍能正常工作               |      |
| FQ-06 | 任务类型 i18n      | 切换语言                                  | 徽章文本正确更新                      |      |

---

## 14. CommandPreview (第 2 阶段)

| ID    | 测试用例         | 步骤                      | 预期结果               | 结果 |
| ----- | ---------------- | ------------------------- | ---------------------- | ---- |
| CP-01 | Auto-editor 类型 | 设置 `type="auto-editor"` | 命令以纯文本形式显示   |      |
| CP-02 | FFmpeg 类型      | 设置 `type="ffmpeg"`      | 原有的语法高亮仍然有效 |      |
| CP-03 | XSS 防护         | 文件路径包含 HTML 标签    | 渲染为纯文本而非 HTML  |      |

---

## 15. AppSettings 往返测试

| ID    | 测试用例   | 步骤                                                         | 预期结果                 | 结果 |
| ----- | ---------- | ------------------------------------------------------------ | ------------------------ | ---- |
| ST-01 | 保存与加载 | 创建带有 `auto_editor_path="/test"` 的设置，保存并加载       | 路径被保留               |      |
| ST-02 | 默认为空   | 创建默认的 AppSettings                                       | `auto_editor_path == ""` |      |
| ST-03 | from_dict  | `AppSettings.from_dict({"auto_editor_path": "/usr/bin/auto-editor"})` | 路径设置正确             |      |

**测试脚本:**

```python
from core.models import AppSettings

# ST-02: 默认
s = AppSettings()
print("ST-02:", s.auto_editor_path == "")

# ST-03: from_dict
s = AppSettings.from_dict({"auto_editor_path": "/usr/bin/auto-editor"})
print("ST-03:", s.auto_editor_path == "/usr/bin/auto-editor")

# ST-01: 往返测试
d = s.to_dict()
s2 = AppSettings.from_dict(d)
print("ST-01:", s2.auto_editor_path == s.auto_editor_path)
```

---

## 16. 端到端场景

### E2E-01: 完整的 Auto Cut 工作流

| 步骤 | 操作                                    | 预期结果                                                | 通过 |
| ---- | --------------------------------------- | ------------------------------------------------------- | ---- |
| 1    | 打开 Settings，设置 auto-editor 路径    | 显示版本，徽章为绿色                                    |      |
| 2    | 导航到 Auto Cut 页面                    | 页面加载，状态栏显示 ready                              |      |
| 3    | 拖入一个有效的 .mp4 文件                | 文件被接受，显示路径                                    |      |
| 4    | 配置 Basic 选项卡 (音频编辑, 阈值 0.04) | 参数设置正确                                            |      |
| 5    | 检查命令预览                            | 显示 `--edit audio:0.04 --progress machine`          |      |
| 6    | 点击 "Add to Queue"                     | 任务已添加，显示确认信息                                |      |
| 7    | 导航到 Task Queue                       | 任务可见，带有 "Auto Cut" 徽章                          |      |
| 8    | 等待任务完成                            | 进度达到 100%，状态 = completed                         |      |
| 9    | 验证输出文件                            | 输出文件存在于预期路径                                  |      |

### E2E-02: 错误处理工作流

| 步骤 | 操作                        | 预期结果                          | 通过 |
| ---- | --------------------------- | --------------------------------- | ---- |
| 1    | 清除 auto-editor 路径       | 设置中的路径被移除                |      |
| 2    | 导航到 Auto Cut 页面        | 状态栏显示 "Set path in Settings" |      |
| 3    | 拖入文件，尝试添加到队列    | 按钮被禁用，无法添加              |      |
| 4    | 前往 Settings，设置无效路径 | 显示错误消息                      |      |
| 5    | 设置有效路径                | 显示版本，徽章为绿色              |      |
| 6    | 返回 Auto Cut，添加任务     | 任务成功添加                      |      |

### E2E-03: 取消与重试工作流

| 步骤 | 操作                          | 预期结果                     | 通过 |
| ---- | ----------------------------- | ---------------------------- | ---- |
| 1    | 将 auto-editor 任务添加到队列 | 任务可见，状态为 pending     |      |
| 2    | 等待任务开始运行              | 状态 = running，进度正在更新 |      |
| 3    | 点击 Cancel                   | 任务状态更改为 cancelled     |      |
| 4    | 验证部分输出是否已清理        | 没有残留的部分输出文件       |      |
| 5    | 重试同一个任务                | 任务从头开始重新启动         |      |

## Phase7-11测试结果

- FP-03测试不通过：有有效auto-editor后，仍然显示“请在设置中配置 auto-editor 路径”
- FP-06测试不通过，有有效auto-editor后仍不可点击
- FB-04  优化方向：到0.1和0.2时显示0.10和0.20避免布局变动
- FB相关优化方向：这些参数都是必须要传入或者这些数值都是默认传入的值吗，不是的话，应该默认设为不传入，选择了相关选项才传入。此外，输入框不要出现消失，选择了不需要输入框的选项时冻结住就行了，这样才能避免排版变动。
- FB-11测试不通过，命令预览没有任何更新。也因此，相关测试无法测试
- FA-04测试不通过，视频/音频编码器下拉框未填充编码器列表  。也因此FA-05无法测试
- FS-02测试不通过，点击不打开文件选择
- FS-03测试不通过，有有效auto-editor后，仍然显示“未配置”。但FS-07测试通过
- FS相关问题，相关的持久化配置是否保存到并读取在：软件目录\data\ 文件夹中

已完成一轮修复，进行第二轮测试，详细内容如下：

## 第二轮测试结果

- FB相关优化不正确：我看到现在静音时和正常时共用了速度和音量输入框，这不对，他们的输入框应该是独立的。而且分别支配一个“速度/音量”输入框即可，输入框选到速度是显示默认值4，选音量时显示默认值0.5
- FP-03优化不完全：有有效auto-editor后，仍然短暂显示“请在设置中配置 auto-editor 路径”过了一秒左右才消失。
- 自动剪辑页面的FileDropInput：点击未弹出文件选择器
- FD-02：应该支持拖入多个，命令预览显示预览占位符即可（始终这样，能够让命令预览在没有输入文件的时候也能够预览命令），添加到队列时分别带着标识符依次传入队列即可
- FQ测试：自动剪辑任务添加到队列之后，任务带有自动剪辑标识，但是执行发现运行的是ffmpeg命令：core.ffmpeg_runner:run_single - Running: C:\Program Files\FFmpeg\ffmpeg.EXE -hide_banner -y -i Q:\Git\GithubManager\ff-intelligent-neo\test_files\20260327Fly.mkv -c:v libx264 -c:a aac -b:a 128k -y Q:\Git\GithubManager\ff-intelligent-neo\test_files\20260327Fly.mp4
- 添加了一次到队列之后，又显示“请在设置中配置 auto-editor 路径”了。好像不是添加到队列的问题，而是设置完之后一切出设置界面设置界面就又“未配置”了，查看本地持久化文件是有auto-editor二进制路径的

---

## 测试环境注意事项

- **auto-editor 二进制文件**: API 测试必须安装 v30.1.4+ 版本
- **测试媒体文件**: 准备一个短的 .mp4 文件 (< 30s) 用于任务测试
- **设置持久化**: 涉及保存/加载的测试需要一个可写的设置目录
- **前端开发服务器**: 运行前端测试需使用 `bun run dev`
- **后端服务器**: 运行 API 测试需使用 `uv run main.py`
