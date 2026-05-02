> - 配置页-剪辑tab下面涉及的功能
> - 自定义页-FFmpeg参数中设计的功能
> - 以上两点涉及的功能在python后端实现上存在明显问题，请你自查之后告诉我出了什么问题

---

## 问题汇总

| # | 严重度 | 问题 | 模块 |
|---|--------|------|------|
| 1 | 严重 | `file_duration` 未传递，extract 模式生成负时间 | 剪辑 |
| 2 | 中等 | docstring 与实际时间格式矛盾 | 剪辑 |
| 3 | 中等 | `add_tasks` 子配置覆盖丢失 | 通用 |
| 4 | 低 | `-y` 参数重复 | 自定义 |
| 5 | 严重 | `-i` 固定在首位，用户输入选项被当作输出选项 | 自定义 |
| 6 | 严重 | 验证强制双端填写 + 空字符串生成无效参数 | 剪辑 |

---

## 问题一：`file_duration` 未传递，extract 模式生成负时间（严重）

**位置**: `core/command_builder.py:661-705`

`build_clip_command` 函数签名接收 `file_duration: float = 0.0` 参数，extract 模式依赖它来计算结束时间：

```python
if clip.clip_mode == "extract":
    end_seconds = file_duration - _parse_time_to_seconds(clip.end_time_or_duration)
    h = int(end_seconds // 3600)
    m = int((end_seconds % 3600) // 60)
    s = end_seconds % 60
    end = f"{h}:{m:02d}:{s:06.3f}"
```

但所有调用方都没有传递这个参数：

- `build_command` 在第 954 行调用 `build_clip_command(config, input_path, output_path)` -- 缺少 `file_duration`
- `build_command_preview` 最终也会走到 `build_command` -- 同样缺失
- `core/task_runner.py` 第 157 行调用 `build_command(task.config, task.file_path, output_path)` -- 也没有传递

**后果**: extract 模式（去掉头尾）下，`file_duration` 默认为 0.0，减去用户输入的尾部时长后得到**负数**，生成的 `-to` 参数是无效的负时间值，FFmpeg 执行必然失败。

**修复方向**: `task_runner.py` 中 `task.duration_seconds` 已通过 `probe_file` 获取，应将其传递给 `build_command`，再转发给 `build_clip_command`。

---

## 问题二：docstring 与实际时间格式矛盾（中等）

**位置**: `core/command_builder.py:569-577`

```python
def _convert_time_to_ffmpeg(time_str: str) -> str:
    """Convert UI time format (H:mm:ss.fff) to FFmpeg format (HH:MM:SS.mmm).

    Replaces the 8th character (colon before ms) with a period.
    Input:  "0:01:30:500" -> Output: "0:01:30.500"
    """
    if not time_str or len(time_str) < 9:
        return time_str
    return time_str[:7] + "." + time_str[8:]
```

docstring 声称输入是 `H:mm:ss.fff`，但示例写的是 `0:01:30:500`（第8位是冒号）。而前端 `ClipForm.vue` 的 `buildTimeString` 实际生成的格式是 `0:01:30.500`（第8位已经是句点）。

当输入为 `0:01:30.500` 时，`time_str[8:]` 已经是 `.500`，函数原样返回，实际上是空操作。虽然最终 FFmpeg 收到的格式恰好正确，但函数的设计意图和实际行为不一致，容易误导后续维护。

---

## 问题三：`add_tasks` 中子配置覆盖导致配置丢失（中等）

**位置**: `main.py:185-219`

`add_tasks` 方法按顺序处理多个子配置（clip、merge、avsmix、custom_command），但每次都是重新创建整个 `TaskConfig`，后者覆盖前者：

```python
if clip_data and ...:
    task_config = TaskConfig(transcode=tc, filters=fc, clip=ClipConfig.from_dict(clip_data), ...)
# ...
if custom_data and ...:
    task_config = TaskConfig(transcode=tc, filters=fc, custom_command=CustomCommandConfig.from_dict(custom_data), ...)
```

如果用户同时配置了 clip 和 custom_command，只有最后一个 `custom_command` 会保留，`clip` 配置丢失。应使用不可变更新方式（如 `dataclasses.replace`）合并子配置。

---

## 问题四：`-y` 参数重复（低）

- `build_clip_command` 不添加 `-y`，依赖 runner 添加
- `build_custom_command` 显式添加了 `-y`，而 runner 也会添加，导致最终命令中出现两个 `-y`

虽然不影响功能（FFmpeg 对重复 `-y` 容忍），但体现了构建逻辑的不一致。

---

## 问题五：自定义命令 `-i` 固定在首位，输入选项被当作输出选项（严重）

**位置**: `core/command_builder.py:915-921`

```python
def build_custom_command(config, input_path, output_path):
    cc = config.custom_command
    args = ["-i", _subprocess_quote(input_path)]       # -i 固定在最前
    if cc.raw_args.strip():
        args.extend(_shlex.split(cc.raw_args.strip()))  # 用户参数全部在 -i 之后
    args.extend(["-y", _subprocess_quote(output_path)])
    return args
```

生成的命令结构：`ffmpeg -hide_banner -y -i input.mp4 [用户所有参数] -y output.mp4`

但 FFmpeg 的参数顺序规则是：
- **输入选项**（`-ss`, `-accurate_seek`, `-f` 等）必须在 `-i` **之前**
- **输出选项**（`-c:v`, `-b:v`, `-filter_complex` 等）在 `-i` **之后**

当用户在 raw_args 中写了 `-accurate_seek` 等输入选项时，它们被强制放在 `-i` 之后，FFmpeg 把它们当作输出选项解析，报错：

```
Option accurate_seek (enable/disable accurate)
applied to output url ... -- you are trying to apply an input option to an output file
Error parsing options for output file ...
Error opening output files: Invalid argument
```

**修复方向**: 使用占位符 `{input}` 让用户控制输入文件在命令中的位置。

FFmpeg 命令结构为 `[输入选项] -i 输入文件 [输出选项] 输出文件`，输入选项和输出选项以 `-i` 为分界。本工具是批处理软件，用户配置时不知道具体输入文件路径（每个任务不同），因此不能让用户直接写 `-i path`。

**方案**: 用户在 raw_args 中用 `{input}` 占位符标记输入文件的插入位置，程序执行时将 `{input}` 替换为 `-i "实际文件路径"`。若 raw_args 中不包含 `{input}`，则在末尾追加 `-i input_path` 作为默认行为。

具体规则:

1. **用户 raw_args 包含 `{input}`**: 程序将 `{input}` 替换为 `-i "实际输入文件路径"`，其余参数保持原样
   - 用户写: `-accurate_seek -ss 00:01:00 {input} -c:v libx264 -b:v 2M`
   - 每个任务替换后: `-accurate_seek -ss 00:01:00 -i "D:\video1.mp4" -c:v libx264 -b:v 2M -y "D:\output1.mp4"`
   - 批处理时每个任务自动替换为各自的输入文件路径

2. **用户 raw_args 不包含 `{input}`**: 程序在末尾追加 `-i input_path`（兼容简单场景）
   - 用户写: `-c:v libx264 -b:v 2M`
   - 生成: `-c:v libx264 -b:v 2M -i "D:\video.mp4" -y "D:\output.mp4"`

**优势**:
- 批处理友好: 模板写一次，每个任务自动替换各自的输入文件
- 用户完全控制参数顺序: 输入选项放 `{input}` 前面，输出选项放 `{input}` 后面
- 向后兼容: 不使用 `{input}` 的旧配置仍能工作（追加到末尾）

**配套改动**:
- 前端 placeholder 提示更新为包含 `{input}` 示例并增加文字说明
- `build_command_preview` 中用 `input.mp4` 替换 `{input}` 用于预览展示

---

## 问题六：剪辑模式验证强制双端填写 + 空字符串生成无效参数（严重）

**验证层** (`core/command_builder.py:1178-1188`):

```python
if config.clip and (config.clip.start_time or config.clip.end_time_or_duration):
    clip = config.clip
    if not clip.start_time:
        issues.append({"level": "error", "param": "start_time",
                        "message": "Clip start time is required."})
    if not clip.end_time_or_duration:
        issues.append({"level": "error", "param": "end_time_or_duration",
                        "message": "Clip end time or duration is required."})
```

验证强制要求 start 和 end 都必须填写，但实际上用户可能只想：
- 只填 start：从第 30 秒开始裁剪到结尾（跳过片头）
- 只填 end：从开头裁剪到第 2 分钟（跳过片尾）

**命令构建层** (`core/command_builder.py:681-694`):

```python
start = _convert_time_to_ffmpeg(clip.start_time)   # 空字符串 -> 返回 ""
# ...
args = ["-ss", start, "-to", end, "-accurate_seek", "-i", ...]
```

当只填一边时，另一边为空字符串 `""`。`_convert_time_to_ffmpeg("")` 因 `len < 9` 直接返回 `""`，导致生成 `-ss "" -to "0:02:00.000"` 这样的无效参数。FFmpeg 无法解析空的 `-ss` 值。

**修复方向**:
1. 验证层应改为：只要求 start 或 end 至少填一个
2. 命令构建层应：只在时间值非空时才添加 `-ss` / `-to` 参数

## 未覆盖的风险点（建议补充审计）

1. **`extract` 模式的语义偏差**：当前 `end_seconds = file_duration - 用户填写的 end_time_or_duration`，即用户填写的是“尾部截去的时长”。但 UI 和变量名 `end_time_or_duration` 暗示该字段可能是结束时间点，两者语义模糊，易用错，可建议审计纳入设计澄清。
---

## 修复记录 (2026-05-02)

### 问题一：✅ 已修复
**修复内容**: 将 `file_duration` 参数通过 `build_command` 传递到 `build_clip_command`。

**修改文件**:
- `core/command_builder.py`: 
  - `build_command` 函数增加 `file_duration: float = 0.0` 参数
  - `build_command` 调用 `build_clip_command` 时传递 `file_duration`
  - `build_clip_command` 递归调用 `build_command` 时传递 `file_duration`
  - `build_command_preview` 调用 `build_command` 时传递默认值 `0.0`
- `core/task_runner.py`:
  - `build_command` 调用传递 `task.duration_seconds` 作为 `file_duration`

**验证**: `task_runner.py` 中 `task.duration_seconds` 已通过 `probe_file` 获取，现在正确传递给命令构建器。

### 问题二：✅ 已修复
**修复内容**: 修正 `_convert_time_to_ffmpeg` 的 docstring，使其与实际行为一致。

**修改文件**:
- `core/command_builder.py`: 
  - docstring 现在正确说明输入格式为 `H:mm:ss.fff`（第8位是句点）
  - 修正示例：`"0:01:30.500"` -> `"0:01:30.500"`（实际输入格式）
  - 说明函数行为：当第8位已是句点时，替换操作是空操作（no-op）

### 问题三：✅ 已修复
**修复内容**: 修复 `add_tasks` 中子配置覆盖丢失问题，使用 `dataclasses.replace` 增量更新。

**修改文件**:
- `main.py`:
  - 导入 `dataclasses` 模块
  - `add_tasks` 方法中，每个子配置块使用 `dataclasses.replace(task_config, ...)` 更新配置
  - 不再每次创建新的 `TaskConfig`，而是基于现有配置更新

**验证**: 现在用户同时配置 clip 和 custom_command 时，两个子配置都会被保留。

### 问题四：✅ 已修复
**修复内容**: 移除 `build_custom_command` 中重复的 `-y` 参数。

**修改文件**:
- `core/command_builder.py`:
  - `build_custom_command` 不再添加 `-y`（runner 会添加）
  - 输出路径直接使用 `args.append()` 而非 `args.extend(["-y", ...])`

### 问题五：✅ 已重新设计
**修复内容**: 重新设计自定义命令的输入选项处理，使用已知 FFmpeg 输入选项列表自动分割用户输入。

**修改文件**:
- `core/command_builder.py`:
  - 新增 `_INPUT_OPTIONS: frozenset[str]` 定义已知 FFmpeg 输入选项
  - 新增 `_split_input_output_args(raw_args)` 函数，自动分割输入/输出选项
  - 修改 `build_custom_command` 使用新的分割逻辑
  - 输入选项（如 `-ss`, `-accurate_seek`) 自动放在 `-i` 之前
  - 输出选项（如 `-c:v`, `-b:v`) 自动放在 `-i` 之后

**已知输入选项列表**:
```
"-ss", "-t", "-to", "-accurate_seek", "-noaccurate_seek",
"-f", "-r", "-s", "-aspect", "-bits_per_raw_sample",
"-thread_queue_size", "-seek_timestamp", "-vsync",
"-dts_delta_threshold", "-dts_error_threshold",
"-init_hw_device", "-filter_hw_device",
"-re", "-loop", "-shortest",
"-hwaccel", "-hwaccel_device", "-hwaccel_output_format",
"-probesize", "-analyzeduration",
"-discard", "-start_at_zero"
```

**注意**: 如果后续遇到未覆盖的输入选项，可将其添加到 `_INPUT_OPTIONS` 集合中。

### 问题六：✅ 已修复
**修复内容**: 修复剪辑模式验证和命令构建，支持只填一端。

**修改文件**:
- `core/command_builder.py`:
  - **验证层**: 移除强制双端填写的检查。现在只要求至少填写一个（`start_time` 或 `end_time_or_duration`）。
  - **extract 模式**: 如果 `end_time_or_duration` 为空，不添加 `-to` 参数
  - **命令构建层**: 
    - 只在 `clip.start_time` 非空时添加 `-ss`
    - 只在 `clip.end_time_or_duration` 非空时添加 `-to`
    - 只在任一参数存在时添加 `-accurate_seek`
    - 输入文件 `-i` 始终添加

**验证**: 
- 只填 `start_time`: 生成 `-ss <start> -accurate_seek -i input`
- 只填 `end_time_or_duration`: 生成 `-to <end> -accurate_seek -i input`（cut 模式）或 `-to <calculated_end> -accurate_seek -i input`（extract 模式）
- 两端都填: 生成 `-ss <start> -to <end> -accurate_seek -i input`

---

## 总结

所有 6 个问题均已修复：
1. ✅ file_duration 传递问题
2. ✅ docstring 矛盾
3. ✅ 子配置覆盖丢失
4. ✅ -y 参数重复
5. ✅ 自定义命令输入选项处理（重新设计）
6. ✅ 剪辑模式部分填写支持

**测试建议**:
1. 测试 extract 模式，确保 `file_duration` 正确传递
2. 测试只填 `start_time` 或只填 `end_time_or_duration` 的剪辑任务
3. 测试自定义命令中同时使用输入选项（`-ss`, `-accurate_seek`）和输出选项（`-c:v`, `-b:v`）
4. 测试同时配置 clip 和 custom_command，确保两者都被保留

# 其他问题

- 配置页-剪辑tab-剪辑模式默认设为时间范围吧，并且剪辑模式提供一下不传入精准剪辑的额外两个模式

  ```
    Summary of Changes (Current Session)
  
    What You Requested
  
    1. Change default clip mode to "time range" (cut)
    2. Add two new modes that are the same as existing ones but without -accurate_seek
  
    Changes Made
  
    Frontend:
    - types/config.ts - Added cut_no_accurate and extract_no_accurate to type union
    - composables/useGlobalConfig.ts - Changed default from "extract" to "cut"
    - components/config/ClipForm.vue - Added two new mode options to selector
    - i18n/locales/zh-CN.ts - Added translations
    - i18n/locales/en.ts - Added translations
  
    Backend:
    - core/command_builder.py - Updated build_clip_command:
      - cut and extract modes: add -accurate_seek (unchanged)
      - cut_no_accurate and extract_no_accurate modes: do NOT add -accurate_seek
      - All modes still add -ss/-to when time values are filled
  
    Behavior:
  
    ┌─────────────────────┬─────────┬────────────────┐
    │        Mode         │ -ss/-to │ -accurate_seek │
    ├─────────────────────┼─────────┼────────────────┤
    │ cut                 │ Yes     │ Yes            │
    ├─────────────────────┼─────────┼────────────────┤
    │ extract             │ Yes     │ Yes            │
    ├─────────────────────┼─────────┼────────────────┤
    │ cut_no_accurate     │ Yes     │ No             │
    ├─────────────────────┼─────────┼────────────────┤
    │ extract_no_accurate │ Yes     │ No             │
    └─────────────────────┴─────────┴────────────────┘
  
    Verification
  
    - Frontend build: pass (2.18s)
    - Backend test: all 4 modes work correctly
  ```

- 当前配置页-剪辑tab与同配置页下的其他设置解耦了，这不对，会导致剪辑tab在任何情况下都不会被队列应用，而且与我们设计的意图不同，配置页所有tab都是一体的，有冲突就解决冲突，但不能解耦

  ```
  Summary of Changes
  
  Problem
  Clip tab was fully decoupled from other config tabs (transcode/filters).
  - Frontend: configRef only included clip when mode === "clip" (mutual exclusion)
  - Backend: build_command dispatched to build_clip_command exclusively, ignoring transcode/filters
  
  Fix Strategy
  Clip parameters (-ss/-to/-accurate_seek) are INPUT-side options that don't conflict
  with OUTPUT-side options (codecs, filters). They can be safely merged.
  - Clip + transcode/filters: MERGE (clip time args injected before -i)
  - Clip + custom_command: MUTUALLY EXCLUSIVE (user controls full command)
  - Clip + merge: MUTUALLY EXCLUSIVE (merge operates on file lists, not single files)
  - Clip use_copy_codec=true: standalone path (no transcode/filters needed)
  
  Frontend Changes (useGlobalConfig.ts):
  - clip config now included whenever data is filled, unless mode is "merge" or "custom"
  - No longer gated by mode === "clip" in the if/else chain
  
  Backend Changes (command_builder.py):
  - Added _build_clip_time_args() helper to extract reusable clip time arguments
  - Refactored build_clip_command to use the helper
  - Modified build_command: clip no longer dispatches exclusively
    - use_copy_codec=true -> standalone clip path (unchanged behavior)
    - use_copy_codec=false -> clip time args merged into main command chain
  - build_command_preview: no changes needed (delegates to build_command)
  
  Verification:
  - Frontend build: pass (1.99s)
  - Backend tests: all 7 scenarios pass
    1. Clip + transcode + resolution: merged correctly
    2. Clip + volume filter: merged correctly
    3. Clip use_copy_codec: standalone, no filters
    4. No clip: baseline unchanged
    5. Preview: reflects merged command
    6. Extract mode: end time calculated correctly (file_duration - tail)
    7. Custom command: clip excluded (mutual exclusion)
  ```

- 我测试功能的时候发现一个问题，任务列表中通过“重置”重新开始的任务，继承的是原本执行时传递的剪辑参数还是之前的，而其他参数则是实时的
  - 这里的逻辑是：**当前任务的 clip 优先**。这意味着如果任务创建时有 clip 配置，重置后重新执行时，即使前端已经删除了 clip 数据，旧值仍然会被保留。
  - 修复方案：**clip 应该用 incoming 优先**（与 transcode/filters 一致），因为 clip 现在是全局配置的一部分。
- 配置-剪辑tab中各个输入框是否限制好了数字范围？添加一个按钮一键清空填入的数字
  - **数字范围限制**：`buildTimeString` 新增 `clamp` 函数，H(0-99)、MM(0-59)、SS(0-59)、ms(0-999)，用户输入超范围值会被自动截断。
  - **清空按钮**：标题行右侧新增"清空"按钮，一键清空开始时间和结束/时长字段。

### 📝 Commit Message

```
feat(clip): 默认切时间范围模式，新增不精准剪辑选项并修复全局配置继承与范围限制

- 默认剪辑模式由 extract 改为 cut（时间范围）
- 增加 cut_no_accurate / extract_no_accurate 两种不带 -accurate_seek 的模式
- 修复 clip 参数在任务重置时未使用 incoming 数据（改为 incoming 优先）
- 剪辑时间输入范围自动截断（H 0-99、MM 0-59、SS 0-59、ms 0-999）并支持一键清空
- 解除剪辑 tab 与其他配置项的互斥，允许 clip 与 transcode/filters 合并应用
```

### 🚀 Release Notes

```
## 2026-05-02 - 剪辑配置与任务继承优化

### ✨ 新增
- 剪辑模式新增“不精准剪辑”选项（cut_no_accurate / extract_no_accurate），可在不启用精准 seek 的情况下裁剪
- 剪辑时间输入支持一键清空，快速重置开始/结束时间
- 剪辑配置不再与其他配置互斥：可同时使用裁剪、转码与滤镜

### 🐛 修复
- 任务“重置”后剪辑参数未更新：现在优先采用当前配置，避免旧值残留
- 剪辑时间范围溢出自动修正：小时/分钟/秒/毫秒均在合法范围内
- extract 模式因缺 file_duration 生成负时间的严重错误

### ⚡ 优化
- 默认剪辑模式调整为“时间范围”（cut），更符合常见使用场景
- 自定义命令的输入选项自动识别并正确排序，避免 -ss/-accurate_seek 等被误作输出选项
- 减少冗余参数：移除重复的 -y 并统一由 runner 控制
- 子配置合并策略优化：使用不可变更新避免 clip/custom_command 等配置相互覆盖
```
