# 业务规则

## 日志生命周期规则

<!-- v2.1.0-CHANGE: 行5-行30 新增日志生命周期规则 -->

| 场景 | 行为 |
|------|------|
| FFmpeg 运行中（running） | 日志实时写入 `task.log_lines`，前端 Log 按钮可查看 |
| FFmpeg 报错退出（failed） | 日志保留不清除，Log 按钮持续可查看 |
| FFmpeg 正常完成（completed） | 日志保留，Log 按钮隐藏（前端不显示） |
| 用户取消（cancelled） | 日志保留，Log 按钮隐藏（前端不显示） |
| 用户 Reset（completed/cancelled） | 清空 log_lines、error、output_path、progress、时间戳 |
| 用户 Retry（failed） | 日志保留，不清除 |
| 手动删除任务 | 同步从内存队列中移除 |
| 重启恢复 | 任务从 APPDATA 恢复，日志截断为最近 100 行 |

### 日志容量

- 每个任务最多保留 100 行日志（`log_lines` 数组上限）
- 日志仅在内存中维护，不持久化到磁盘文件

## Download FFmpeg 二次确认规则

<!-- v2.1.0-CHANGE: 行35-行50 新增下载确认规则 -->

| 规则 | 说明 |
|------|------|
| 按钮可见性 | Download FFmpeg 按钮始终可见，不受 FFmpeg 当前状态影响 |
| 二次确认 | 点击后弹出 DaisyUI modal 对话框："This will download FFmpeg and overwrite the current version. Continue?" |
| 取消操作 | 点击 Cancel 或点击背景遮罩关闭对话框，不触发下载 |
| 确认操作 | 点击 Confirm 触发 `download` 事件给父组件处理 |
| 加载状态 | 下载中按钮显示 loading spinner，禁用点击，5 秒后自动恢复 |
| 检测中禁用 | FFmpeg 正在检测时（status=detecting），下载按钮禁用 |

## FFmpeg 版本切换事件规则

<!-- v2.1.0-CHANGE: 行55-行68 新增版本切换事件规则 -->

| 规则 | 说明 |
|------|------|
| 事件名称 | `ffmpeg_version_changed` |
| 触发时机 | `switch_ffmpeg` 后端方法调用成功时 |
| 事件数据 | `{ version: string, path: string, status: 'ready' }` |
| 前端监听 | `AppNavbar.vue` 通过 `onEvent` 监听此事件 |
| 更新内容 | 导航栏 FFmpeg 状态徽标实时更新版本号和状态 |

## Reset 行为规则

<!-- v2.1.0-CHANGE: 行73-行88 新增 Reset 业务规则 -->

| 规则 | 说明 |
|------|------|
| 适用状态 | 仅 `completed` 和 `cancelled` 状态可执行 Reset |
| 目标状态 | Reset 后任务变为 `pending` |
| 自动执行 | Reset 不自动开始任务，需用户手动点击 Start |
| 数据清理 | 清空：error, log_lines, output_path, progress, started_at, completed_at |
| 数据保留 | 保留：id, file_path, file_name, file_size_bytes, duration_seconds, config |
| 前端触发 | `useTaskControl.ts` 的 `resetTask(id)` 调用后端 `reset_task(id)` |

## 主题切换规则

<!-- v2.1.0-CHANGE: 行93-行108 新增主题规则 -->

| 规则 | 说明 |
|------|------|
| 支持主题 | `auto`（跟随系统）、`light`、`dark` |
| 实现方式 | 通过 `document.documentElement.setAttribute("data-theme", resolved)` 切换 |
| 持久化 | 保存到 `settings.json` 的 `theme` 字段 |
| 自动检测 | auto 模式下通过 `window.matchMedia("(prefers-color-scheme: light)")` 检测 |
| 实时监听 | auto 模式下监听 `matchMedia` change 事件，系统主题变化时自动更新 |
| UI 入口 | 导航栏右侧太阳/月亮图标按钮，`toggleTheme()` 在 light/dark 间切换 |

## 文件拖拽输入规则

<!-- v2.1.0-CHANGE: 行113-行130 新增 FileDropInput 规则 -->

| 规则 | 说明 |
|------|------|
| 组件 | `FileDropInput.vue`（`frontend/src/components/common/`） |
| 输入方式 | 拖拽文件到区域 或 点击打开文件选择器 |
| 文件类型验证 | 前端通过 `accept` prop（如 `.png,.jpg`）验证扩展名 |
| 拖拽延迟 | drop 后等待 80ms 再调用 `get_dropped_files`（兼容 pywebvue 事件冒泡） |
| 显示内容 | 有值时显示文件名（非完整路径），鼠标悬停显示完整路径 |
| 清除操作 | 右侧 X 按钮清空已选文件 |
| 错误提示 | 类型不匹配时在区域内显示红色错误文本 |
| 使用场景 | 水印路径（FilterForm.vue）、横竖屏背景图片（预留） |

---

## Phase 3: 命令构建功能业务规则

<!-- v2.1.0-CHANGE: Phase 3 新增命令构建相关业务规则 -->

### 编码器选择规则

| 规则 | 说明 |
|------|------|
| 分组显示 | 编码器按优先级分组：P0 首选推荐 / P1 次选推荐 / P2 条件推荐 |
| 硬件检测 | 启动时通过 `check_hw_encoders()` 检测 FFmpeg 可用编码器 |
| 灰显处理 | 不在检测结果中的硬件编码器灰显，tooltip 显示"未检测到此硬件编码器" |
| 自动填充 | 选择编码器后自动填充推荐的 quality_value 和 quality_mode |
| 手动调整 | 用户可手动修改质量值，但超出合理范围时显示 warning |
| 质量值范围 | CRF: 0-51, CQ: 0-51, QP: 0-51, 0=无损/最高质量 |
| 编码器验证 | `validate_config` 校验编码器名称是否在 VALID_VIDEO/AUDIO_CODECS 集合中 |

<!-- v2.1.0-CHANGE: Phase 3.5 新增自定义编码器输入规则 -->

### 自定义编码器输入规则

| 规则 | 说明 |
|------|------|
| 入口 | EncoderSelect 下拉列表底部提供 "Other (custom name)..." 选项 |
| 输入方式 | 选中后显示文本输入框，用户键入任意 FFmpeg 编码器名称 |
| 质量参数 | 自定义编码器不自动填充 quality_mode / quality_value，用户需手动设置 |
| 硬件检测 | 自定义编码器跳过 supportedEncoders 检测，始终可选 |
| 验证 | 自定义编码器仍需通过 `validate_config` 的基本校验（非空字符串） |

### 编码质量参数规则

<!-- v2.1.0-CHANGE: Phase 3.5 新增质量参数业务规则 -->

| 规则 | 说明 |
|------|------|
| quality_mode | 支持值: crf, cq, qp。对应 FFmpeg -crf/-cq/-qp 参数 |
| quality_value | 数值范围 0-51。CRF/CQ 越低质量越高，QP 越高质量越高。0 = 禁用 |
| 自动填充 | 从编码器注册表的 recommendedQuality 和 qualityMode 自动填充 |
| copy/none 跳过 | 当 video_codec 为 copy 或 none 时，所有质量参数不生成命令参数 |
| preset | 编码速度预设：ultrafast ~ veryslow。映射 FFmpeg -preset 标志 |
| pixel_format | 像素格式：yuv420p（兼容性最佳）、yuv420p10le（HDR/10-bit）、yuv422p、yuv444p |
| max_bitrate | 最大码率限制：格式如 `8M`。映射 -maxrate 标志，需配合 bufsize |
| bufsize | 缓冲区大小：格式如 `2M`。映射 -bufsize 标志。max_bitrate 设置但 bufsize 为空时默认 2M |
| 仅视频 | quality_mode, quality_value, preset, pixel_format, max_bitrate, bufsize 仅在 video_codec 非 copy/none 时生效 |

### 音频归一化规则

| 规则 | 说明 |
|------|------|
| 与 volume 互斥 | 启用 audio_normalize 时，volume 调整应被忽略或禁用 |
| 默认参数 | I=-16 LUFS, TP=-1.5 dBTP, LRA=11 LU（EBU R128 标准） |
| 滤镜位置 | 在滤镜链中位于 speed 之前、watermark 之后（priority 16） |
| 质量影响 | loudnorm 会重新编码音频流，不可与 `-c:a copy` 同时使用 |
| 两遍模式 | Phase 3 使用单遍 loudnorm（简化实现），如需精确归一化后续可扩展为两遍 |
| 音频码率默认 | audio_bitrate 默认值从 Phase 3.5.1 起改为 128k（原 192k） |

<!-- v2.1.0-CHANGE: Phase 3.5.1 新增滤镜互斥清理规则 -->

### 滤镜互斥清理规则

| 规则 | 说明 |
|------|------|
| 自动清理 | 选择 aspect_convert 时自动清空 rotate；选择 rotate 时自动清空 aspect_convert |
| 防冻结 | 修复此前两个选项同时被禁用的 bug，确保始终可以取消选择 |
| UI 反馈 | 被禁用的选项灰显并显示 tooltip 说明原因 |

### 变速规则

<!-- v2.1.0-CHANGE: Phase 3.5.1 更新变速范围规则 -->

| 规则 | 说明 |
|------|------|
| 有效范围 | 0.25 - 4.0（硬限制，超出范围返回 error） |
| 警告范围 | 0.5 - 2.0 以外的值触发 warning（可能导致音视频不同步） |
| atempo 限制 | FFmpeg atempo 单次范围 0.5-100.0，但实际使用中 >4.0 体验不佳 |
| 音频处理 | 超出 0.5-2.0 范围时自动链式 atempo 滤镜 |

### 横竖屏转换规则

| 规则 | 说明 |
|------|------|
| 与基础滤镜互斥 | 启用 aspect_convert 时，crop/rotate/watermark 应被禁用 |
| I 模式依赖 | H2V-I 和 V2H-I 模式必须提供 bg_image_path，否则验证不通过 |
| 分辨率默认 | 竖屏默认 1080x1920，横屏默认 1920x1080 |
| 滤镜位置 | 在滤镜链中位于 rotate 之后、watermark 之前（priority 35） |
| filter_complex | 所有横竖屏转换均使用 -filter_complex，需要额外的流输入（背景图片） |
| 分辨率格式 | UI 使用 'x'（1080x1920），FFmpeg 内部转换为 ':'（1080:1920） |

### 视频剪辑规则

| 规则 | 说明 |
|------|------|
| 提取模式 | 需要获取文件时长（ffprobe），end_time = duration - tail_duration |
| 精确剪切 | 用户直接指定 start 和 end 时间戳 |
| 时间格式 | UI: `H:mm:ss.fff`，FFmpeg: `HH:MM:SS.mmm`（第8个字符冒号替换为点号） |
| -accurate_seek | 始终启用，优先可靠性而非帧精度 |
| copy 模式 | 默认 `-c copy` 无损快速剪辑，要求编码参数一致 |
| 非 copy 模式 | 禁用 copy 时使用当前 TranscodeConfig 重新编码 |
| 时间验证 | start_time < end_time（cut 模式），start_time < file_duration（extract 模式） |
| 与其他功能互斥 | 剪辑功能独立于转码/滤镜配置，不在同一命令中叠加 |
<!-- v2.1.0-CHANGE: Phase 3.5 新增条件包含规则 -->
| 条件包含 | 当 start_time 和 end_time_or_duration 均为空时，不生成剪辑命令参数，也不传递 clip 配置给 build_command |

### 音频字幕混合规则

| 规则 | 说明 |
|------|------|
| 独立功能 | 与转码/滤镜配置可叠加使用 |
| 音频替换 | replace_audio=True 时：`-map 0:v -map 1:a`，替换原始音频 |
| 字幕嵌入 | `-c:s mov_text -metadata:s:s:0 language=xxx`，使用 MP4 容器支持 |
| 多输入 | 需要 `-i` 额外输入文件（音频和/或字幕），通过 -map 映射流 |
| 文件验证 | external_audio_path 必须是有效音频文件，subtitle_path 必须是 .srt/.ass/.ssa |
| FileDropInput | 两个路径输入均使用 FileDropInput 组件 |

### 多视频拼接规则

| 规则 | 说明 |
|------|------|
| 最少文件 | 至少 2 个视频文件才能拼接 |
| 默认模式 | Merge 页面默认 `concat_protocol`，Config 页面 Intro/Outro 默认 `filter_complex` |
| concat_protocol | concat demuxer: `-f concat -safe 0 -i list.txt -c copy`，要求相同编码参数 |
| ts_concat | concat demuxer: `-f concat -safe 0 -i list.txt -c copy`，与 concat_protocol 使用相同底层机制 |
| 降级策略 | ts_concat/concat_protocol 失败时降级到 filter_complex 模式 |
| filter_complex | 支持不同编码参数的文件，可指定目标分辨率/帧率/编码器进行标准化 |
| concat URL 协议 | **不推荐**: `concat:file1|file2` URL 协议不适用于 MP4 容器（仅 .ts 等基础流格式有效），且在 Windows 上因路径 `D:` 与协议前缀冲突而解析失败。改用 concat demuxer |
| concat 滤镜输入 | concat 滤镜输入必须按 video/audio 交错排列: `[v0][a0][v1][a1]...concat=n=N:v=1:a=1[vout][aout]` |
<!-- v2.1.0-CHANGE: Phase 3.5 更新 filter_complex 默认值规则 -->
| filter_complex 默认值 | 当 target_resolution 为空时默认 1920x1080，target_fps 为 0 时默认 30，setsar=1 始终包含 |
| 文件顺序 | 拼接顺序严格按文件列表顺序，支持拖拽排序调整 |
| 输出路径 | 输出到第一个文件所在目录，文件名自动生成 |
| 临时列表文件 | concat demuxer 的 `list.txt` 由 `task_runner.py` 在运行时创建，任务完成后自动清理 |
| 与其他功能互斥 | 拼接功能独立，不在同一命令中叠加转码/滤镜/剪辑配置 |

<!-- v2.1.0-CHANGE: Phase 3.5 新增片头片尾规则 -->

### 拼接片头片尾规则

| 规则 | 说明 |
|------|------|
| 字段 | MergeConfig 的 intro_path 和 outro_path |
| 模式限制 | 仅 filter_complex 模式支持片头片尾，其他模式忽略此配置 |
| 强制模式 | 设置 intro_path 或 outro_path 时，自动强制 merge_mode 为 filter_complex |
| 全局生效 | Config 页面设置的 intro/outro 通过全局 `configRef` 应用于所有队列任务（无论从哪个页面添加） |
| 输入顺序 | Input 0 = intro（如设置），Input 1 = 内容视频，Input 2 = outro（如设置） |
| 标准化 | 所有输入均经过 fps/scale/setsar 标准化后 concat |
| concat 滤镜输入 | 必须交错排列: `[0:v]fps...setsar=1[v0];[0:a]aformat...[a0];[1:v]...[v1];[1:a]...[a1];[v0][a0][v1][a1]...concat=n=N:v=1:a=1[vout][aout]` |
| 不要求文件列表 | intro/outro 独立使用时不需要 file_list（validate_config 在 intro/outro 有值时跳过 "at least 2 files" 检查） |
| 命令预览 | 使用第一个内容文件作为预览占位符 |
| Merge 页面隔离 | Merge 页面的 merge_config 与 Config 页面的 intro/outro 设置完全独立，互不影响 |
| Task Config 保护 | `start_task` 在更新配置时保留任务已有的子配置，避免 intro/outro 覆盖 merge 任务配置 |

<!-- v2.1.0-CHANGE: Phase 3.5 新增页面布局规则 -->

### 页面布局规则

| 规则 | 说明 |
|------|------|
| 独立页面 | A/V Mix、Merge、Custom Command 各自有独立路由页面 |
| 继承配置 | A/V Mix 和 Merge 页面继承全局 TranscodeConfig，不显示转码 UI |
| 命令预览 | 每个独立页面均有自己的 CommandPreview 组件 |
| Config 页面 | 仅保留 Transcode、Filters、Clip 三个选项卡 |
| 预览位置 | CommandConfigPage 的命令预览移至页面顶部（预设选择器之上） |
| 导航栏 | AppNavbar 新增 "A/V Mix"、"Merge"、"Custom" 导航项 |

<!-- v2.1.0-CHANGE: Phase 3.5 新增自定义命令规则 -->

### 自定义命令规则

| 规则 | 说明 |
|------|------|
| 独立页面 | CustomCommandPage 独立路由 `/custom-command` |
| 输入方式 | 原始 FFmpeg 参数文本域，用户自由输入 |
| 输出扩展 | 可选择输出文件扩展名（默认 .mp4） |
| 命令模板 | `ffmpeg -hide_banner -y -i "input.mp4" {用户参数} -y "output{ext}"` |
| 预览 | 实时预览完整命令，但不调用 build_command（参数由用户直接控制） |
| 优先级 | activeMode="custom" 时，toTaskConfig 优先生成 custom_command 配置 |

<!-- v2.1.0-CHANGE: Phase 3.5.1 新增路径引用规则 -->

### 命令路径引用规则

| 规则 | 说明 |
|------|------|
| 子进程路径 | subprocess.Popen 以列表传递参数时，路径作为独立列表元素传递，不需要 shell 级别引用 |
| Windows 兼容 | 避免使用 `shlex.quote`（在 Windows 上产生单引号包裹导致 "Illegal byte sequence" 错误） |
| 预览引用 | 预览字符串中使用 `shlex.quote` 确保显示可读的命令行 |
| filter_complex | filter_complex 参数值中的路径不做额外引用 |
| 空格路径 | 子进程列表形式自动处理含空格路径 |

<!-- v2.1.0-CHANGE: Phase 3.5.1 更新页面布局规则 -->

### 页面布局规则

| 规则 | 说明 |
|------|------|
| 独立页面 | A/V Mix、Merge、Custom Command 各自有独立路由页面 |
| 继承配置 | A/V Mix 和 Merge 页面继承全局 TranscodeConfig，不显示转码 UI |
| 命令预览 | 每个独立页面均有自己的 CommandPreview 组件 |
| Config 页面 | Transcode、Filters、Clip、Merge 四个选项卡同时只显示一个（互斥显示） |
| 三栏布局 | Config 页面每个表单内部使用 3 列网格布局，缩短纵向长度 |
| 预览位置 | CommandConfigPage 的命令预览移至页面顶部（预设选择器之上） |
| 导航栏 | AppNavbar 新增 "A/V Mix"、"Merge"、"Custom" 导航项 |
| Merge 独立提交 | Merge 页面有 "Add to Queue" 按钮，可独立将合并任务添加到队列 |
| A/V Mix 半屏拖拽 | 音频和字幕各占半屏，使用 SplitDropZone 左右分屏拖放 |
| 水印全屏拖放 | 水印文件支持全屏拖放上传 |
| 水印冻结 | 选择 aspect_convert 时自动清空并冻结 watermark_path |
| Intro/Outro 位置 | 片头片尾从 Merge 页面移至 Config 页面的 Merge 选项卡 |
| Intro/Outro 拖拽 | 使用 SplitDropZone 左半屏拖入 Intro，右半屏拖入 Outro |
| Config 默认选项卡 | 进入 Config 页面时始终切换到 Transcode 选项卡 |

<!-- v2.1.0-CHANGE: Phase 3.5.2 新增分辨率拆分规则 -->

### 分辨率输入规则

| 规则 | 说明 |
|------|------|
| UI 拆分 | Resolution 输入从单一文本框改为 W x H 双数字输入框（TranscodeForm 和 MergeSettingsForm 均适用） |
| 默认值 | Merge 默认 1920x1080，Transcode 留空表示原始分辨率 |
| 双向绑定 | 使用 computed get/set 实现拆分/合并，保持 config.resolution 为 "WxH" 字符串 |
| 清空逻辑 | 切换到 copy/none 时清空 resolution |

<!-- v2.1.0-CHANGE: Phase 3.5.2 新增时间输入拆分规则 -->

### 时间输入规则

| 规则 | 说明 |
|------|------|
| UI 拆分 | 时间输入从单一文本框改为 H:MM:SS.ms 四个独立数字输入框 |
| 格式 | config 存储为 "H:MM:SS.mmm" 字符串，与 FFmpeg 兼容 |
| 可选性 | StartTime 和 EndTime 均为可选（至少提供一个才生成剪辑命令） |
| 对齐布局 | StartTime 和 EndTime 在 ClipForm 中并排显示（md:grid-cols-2） |
| 占位符 | H(0-99), MM(0-59), SS(0-59), ms(0-999) |

| 规则 | 说明 |
|------|------|
| 统一入口 | 所有模式（转码、剪辑、拼接、音频字幕混合）均通过 build_command 生成预览 |
| 参数同步 | 预览使用的配置与实际执行时传入的配置完全一致 |
| 实时更新 | 配置变更时命令预览自动更新（已有 300ms debounce） |

<!-- v2.1.0-CHANGE: Phase 4 新增规则 -->

## Phase 4: 国际化与平台化业务规则

### 语言切换规则

| 规则 | 说明 |
|------|------|
| 支持语言 | zh-CN（简体中文）、en（英文） |
| 默认语言 | auto（跟随系统语言，中文优先） |
| 切换方式 | 导航栏语言切换按钮（EN/CN 标签，点击切换） |
| 持久化 | save_settings({ language: "zh-CN" \| "en" })，持久化到 settings.json |
| auto 模式 | 跟随 navigator.language，优先匹配 zh-CN，其余回退到 en |
| 框架 | vue-i18n v9+，Composition API 模式（legacy: false） |
| 翻译键 | 扁平点分隔命名空间：nav., ffmpeg., settings., taskQueue., config., avMix., merge., custom., common. |

### FFmpeg 下载按钮平台规则

| 平台 | 行为 | 说明 |
|------|------|------|
| Windows (win32) | 显示 "Download FFmpeg" 按钮 | 使用 static_ffmpeg 包下载预编译二进制 |
| macOS (darwin) | 显示 homebrew 安装提示 | "brew install ffmpeg"，附带 brew.sh 链接 |
| Linux (ubuntu/debian) | 显示 apt 安装提示 | "sudo apt install ffmpeg" |
| Linux (fedora) | 显示 dnf 安装提示 | "sudo dnf install ffmpeg" |
| Linux (arch/manjaro) | 显示 pacman 安装提示 | "sudo pacman -S ffmpeg" |
| Linux (其他) | 显示通用提示 | "Install ffmpeg via your package manager" |
| 打包环境 | 所有平台禁用下载 | is_frozen() 时 static_ffmpeg 不可用 |
| 后端守卫 | download_ffmpeg() 检查 sys.platform | 非 Windows 返回 download_not_supported 错误 + 安装指引 |

### 数据目录规则

| 规则 | 说明 |
|------|------|
| 统一目录 | 所有持久化数据保存到 `<app_dir>/data/` |
| app_dir 定义 | PyInstaller 打包时为 exe 所在目录，开发时为项目根目录 |
| 子目录 | `data/settings.json`（配置）、`data/logs/`（日志）、`data/presets/`（预设） |
| 迁移策略 | copy-not-move：从旧 APPDATA 路径复制到新路径，保留旧文件作为备份 |
| 迁移时机 | 首次启动时检测新路径不存在且旧路径存在时执行，一次性迁移 |
| 日志迁移 | 日志不迁移（7天轮转自动清理，无长期价值） |
| 集中管理 | 新增 `core/paths.py` 模块，所有路径通过该模块获取 |
| 初始化顺序 | `main.py` 在所有 core 模块导入之前调用 `paths.migrate_if_needed()` |
