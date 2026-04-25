```
  v2.1.1 Implementation Complete

  Phase 1: Command Preview Performance

  ┌──────┬─────────────────────────┬───────────────────────────────────────────────────────────────────────────┐
  │ Task │          File           │                                  Change                                   │
  ├──────┼─────────────────────────┼───────────────────────────────────────────────────────────────────────────┤
  │ 1.1  │ main.py                 │ New preview_command API (merged validate + build, single IPC)             │
  ├──────┼─────────────────────────┼───────────────────────────────────────────────────────────────────────────┤
  │ 1.1  │ core/command_builder.py │ ValidationContext gains preview_mode, watermark skips Path.exists() check │
  ├──────┼─────────────────────────┼───────────────────────────────────────────────────────────────────────────┤
  │ 1.2  │ useCommandPreview.ts    │ Race condition protection (monotonic requestId)                           │
  ├──────┼─────────────────────────┼───────────────────────────────────────────────────────────────────────────┤
  │ 1.3  │ useCommandPreview.ts    │ Removed deep: true, debounce 300->500ms, in-flight guard                  │
  ├──────┼─────────────────────────┼───────────────────────────────────────────────────────────────────────────┤
  │ 1.4  │ TranscodeForm.vue       │ Object.assign batch field clearing                                        │
  ├──────┼─────────────────────────┼───────────────────────────────────────────────────────────────────────────┤
  │ 1.5  │ useGlobalConfig.ts      │ Confirmed mode-aware filtering already correct                            │
  ├──────┼─────────────────────────┼───────────────────────────────────────────────────────────────────────────┤
  │ 1.6  │ MergeFileList.vue       │ Dragover only visual, emit on dragend; :key uses unique IDs               │
  └──────┴─────────────────────────┴───────────────────────────────────────────────────────────────────────────┘

  Phase 2: UX Reliability

  ┌──────┬───────────────────────────────────────┬───────────────────────────────────────────────────────────────────┐
  │ Task │                 File                  │                              Change                               │
  ├──────┼───────────────────────────────────────┼───────────────────────────────────────────────────────────────────┤
  │ 2.1  │ ClipForm/MergeFileList/PresetSelector │ Error feedback via DaisyUI alert (3s auto-dismiss, i18n)          │
  ├──────┼───────────────────────────────────────┼───────────────────────────────────────────────────────────────────┤
  │ 2.2  │ TaskToolbar/BatchControlBar           │ DaisyUI modal confirm for remove/clear/stopAll                    │
  ├──────┼───────────────────────────────────────┼───────────────────────────────────────────────────────────────────┤
  │ 2.3  │ PresetSelector                        │ Native confirm() replaced with DaisyUI modal                      │
  ├──────┼───────────────────────────────────────┼───────────────────────────────────────────────────────────────────┤
  │ 2.4  │ CommandPreview                        │ "Copied!" feedback + clipboard fallback (textarea+execCommand)    │
  ├──────┼───────────────────────────────────────┼───────────────────────────────────────────────────────────────────┤
  │ 2.5  │ FFmpegSetup                           │ Event-driven download (listen ffmpeg_version_changed, no 5s       │
  │      │                                       │ timeout)                                                          │
  └──────┴───────────────────────────────────────┴───────────────────────────────────────────────────────────────────┘

  Phase 3: Backend Responsiveness

  ┌──────┬────────────────────┬─────────────────────────────────────────────────────────────────────────┐
  │ Task │        File        │                                 Change                                  │
  ├──────┼────────────────────┼─────────────────────────────────────────────────────────────────────────┤
  │ 3.1  │ main.py            │ add_tasks probe_file async (background thread, task_info_updated event) │
  ├──────┼────────────────────┼─────────────────────────────────────────────────────────────────────────┤
  │ 3.2  │ command_builder.py │ validate_config returns [{param, message}] structured errors            │
  ├──────┼────────────────────┼─────────────────────────────────────────────────────────────────────────┤
  │ 3.3  │ command_builder.py │ Watermark validate skips Path.exists() when preview_mode=True           │
  └──────┴────────────────────┴─────────────────────────────────────────────────────────────────────────┘

  Phase 4: Code Quality

  ┌──────┬──────────────────────────────┬────────────────────────────────────────────┐
  │ Task │             File             │                   Change                   │
  ├──────┼──────────────────────────────┼────────────────────────────────────────────┤
  │ 4.1  │ useTaskQueue/useTaskProgress │ Runtime type guards on all bridge events   │
  ├──────┼──────────────────────────────┼────────────────────────────────────────────┤
  │ 4.3  │ useTheme/useLocale           │ Fixed floating promises (.catch())         │
  ├──────┼──────────────────────────────┼────────────────────────────────────────────┤
  │ 4.4  │ TaskQueuePage/useTaskQueue   │ Removed all console.log                    │
  ├──────┼──────────────────────────────┼────────────────────────────────────────────┤
  │ 4.5  │ MergeFileList                │ :key="index" -> :key="getFileKey(file)"    │
  ├──────┼──────────────────────────────┼────────────────────────────────────────────┤
  │ 4.6  │ MergeFileList/FFmpegSetup    │ i18n for hardcoded title/close strings     │
  ├──────┼──────────────────────────────┼────────────────────────────────────────────┤
  │ 4.7  │ PresetSelector               │ loading ref now used in template (spinner) │
  ├──────┼──────────────────────────────┼────────────────────────────────────────────┤
  │ 4.8  │ AppAbout                     │ Module-level t() -> computed               │
  └──────┴──────────────────────────────┴────────────────────────────────────────────┘

  Phase 5: Polish

  ┌──────┬───────────────┬────────────────────────────────────────────────────┐
  │ Task │     File      │                       Change                       │
  ├──────┼───────────────┼────────────────────────────────────────────────────┤
  │ 5.2  │ router.ts     │ 404 catch-all route /:pathMatch(.*)* -> redirect / │
  ├──────┼───────────────┼────────────────────────────────────────────────────┤
  │ 5.3  │ ComboInput    │ Escape key closes dropdown                         │
  ├──────┼───────────────┼────────────────────────────────────────────────────┤
  │ 5.4  │ AppNavbar     │ FFmpeg badge initial unknown (gray), no red flash  │
  ├──────┼───────────────┼────────────────────────────────────────────────────┤
  │ 5.7  │ TranscodeForm │ Empty <div> -> invisible + aria-hidden             │
  └──────┴───────────────┴────────────────────────────────────────────────────┘

  Docs Updated

  - docs/Structure.md - v2.1.1 section appended
  - docs/BusinessRules.md - v2.1.1 rules appended
  - docs/Procedure.md - Flows rewritten + v2.1.1 section appended
  - PRD-2.1.1.md Appendix A - Updated to "completed" status

  Build Verification

  - TypeScript: vue-tsc --noEmit passes (0 errors)
  - Vite build: succeeds (3.25s)
  - Python: py_compile passes for main.py and command_builder.py
```

### CC-Mem

```
     Legend: session-request | 🔴 bugfix | 🟣 feature | 🔄 refactor | ✅ change | 🔵 discovery | ⚖️ decision

     Column Key
       Read: Tokens to read this observation (cost to learn it now)
       Work: Tokens spent on work that produced this record ( research, building, deciding)

     Context Index: This semantic index (titles, types, files, tokens) is usually sufficient to understand past work.

     When you need implementation details, rationale, or debugging context:
       - Fetch by ID: get_observations([IDs]) for observations visible in this index
       - Search history: Use the mem-search skill for past decisions, bugs, and deeper research
       - Trust this index over re-reading code for past decisions and learnings

     Context Economics
       Loading: 50 observations (10,466 tokens to read)
       Work investment: 0 tokens spent on research, building, and decisions

     Apr 23, 2026

     #S2 ComboInput component enhanced with improved filtering behavior (Apr 23, 12:50 AM)

     #S1 Audio transcoding parameter consistency fix - user requested explanation of changes made to ensure passed
     parameters match command preview (Apr 23, 12:50 AM)


     Apr 25, 2026

     #S3 Frontend Code Review for UX Issues and FFmpeg Preview Optimization (Apr 25, 2:04 PM)

     frontend/src/components/config/ClipForm.vue
       #2173  5:00 PM  🔵  ClipForm.vue imports verified as compatible with alertMessage ref addition
       #2174  5:01 PM  🔵  ClipForm.vue template structure examined for alert message placement
       #2175           🟣  ClipForm.vue template updated with error alert display component
     frontend/src/components/config/PresetSelector.vue
       #2176           🔵  PresetSelector.vue imports include ref for potential error state management
     ..\..\Git\GithubManager\ff-intelligent-neo\frontend\src\components\config\PresetSelector.vue
       #2177  9:47 PM  🔄  Replaced browser confirm with modal dialog in PresetSelector
       #2178           🔄  Added loading state and error display to PresetSelector UI
       #2179           🔄  Wired delete button to new modal confirmation flow
       #2180  9:48 PM  🟣  Added delete confirmation modal to PresetSelector
     ..\..\Git\GithubManager\ff-intelligent-neo\frontend\src\components\config\MergeFileList.vue
       #2181           🔄  Added error handling to MergeFileList addFiles function
     references/PRD-2.1.1.md
       #2182  9:53 PM  ⚖️  Adopted document-first development approach for version 2.1.1
     frontend/src/components/task-queue/BatchControlBar.vue
       #2185  9:54 PM  🟣  Added confirmation dialog for batch stop all action
     main.py
       #2193  9:59 PM  🔵  Examined add_tasks method implementation in main.py
       #2197  10:02 PM  🔵  Analyzed add_tasks method implementation details
     frontend/src/bridge.ts
       #2200  10:04 PM  🔵  Examined bridge.ts pywebview initialization logic
     frontend/src/composables/useTaskQueue.ts
       #2201            🔵  Analyzed frontend event handling patterns in composables
       #2204  10:06 PM  🔵  Examined queue_changed event handler pattern
     ..\..\Git\GithubManager\ff-intelligent-neo\frontend\src\i18n\locales\zh-CN.ts
       #2220  10:17 PM  🟣  Added file list action labels for merge page
     ..\..\Git\GithubManager\ff-intelligent-neo\frontend\src\i18n\locales\en.ts
       #2221            🟣  Located fileList section in English locale file
       #2222  10:18 PM  🔵  Read current English fileList translations
       #2223            🟣  Added English translations for file list actions
     ..\..\Git\GithubManager\ff-intelligent-neo\frontend\src\components\settings\FFmpegSetup.vue
       #2224            🔵  Located close button pattern in FFmpegSetup component
       #2225            🔴  Fixed hardcoded close button text in FFmpegSetup
     ..\..\Git\GithubManager\ff-intelligent-neo\frontend\src\components\settings\AppAbout.vue
       #2226  10:19 PM  🔵  Examined AppAbout component structure
       #2227            🔄  Made AppAbout items reactive with computed property
     ..\..\Git\GithubManager\ff-intelligent-neo\frontend\src\pages\TaskQueuePage.vue
       #2229  10:20 PM  🔵  Examined unused variable context in TaskQueuePage
       #2230            🔴  Removed unused variable in TaskQueuePage handleAddFiles
     General
       #2232  10:22 PM  🔵  Task 7 status updated to in_progress
       #2233            🔵  Task 6 marked as completed
     ..\..\Git\GithubManager\ff-intelligent-neo\frontend\src\components\common\ComboInput.vue
       #2234  10:23 PM  🔵  Examined ComboInput component implementation
       #2235            🔵  Examined component patterns for file list implementation
     General
       #2236            🔵  Located application router configuration
     ..\..\Git\GithubManager\ff-intelligent-neo\frontend\src\router.ts
       #2237            🔵  Examined Vue Router configuration
       #2238            🟣  Added catch-all route for 404 handling
     ..\..\Git\GithubManager\ff-intelligent-neo\frontend\src\components\layout\AppNavbar.vue
       #2239            🔄  Refactored FFmpeg status state in AppNavbar
     ..\..\Git\GithubManager\ff-intelligent-neo\frontend\src\components\config\TranscodeForm.vue
       #2240            🟣  Added accessibility attributes to layout placeholder
     ..\..\Git\GithubManager\ff-intelligent-neo\frontend\src\components\common\ComboInput.vue
       #2241            🟣  Added Escape key handler to ComboInput dropdown
     ..\..\Git\GithubManager\ff-intelligent-neo\frontend\src\components\layout\AppNavbar.vue
       #2242            🔄  Updated FFmpeg status initialization in AppNavbar
       #2243            🔄  Updated FFmpeg status event handler in AppNavbar
       #2244  10:24 PM  🔄  Updated FFmpeg status badge template in AppNavbar
     ..\..\Git\GithubManager\ff-intelligent-neo\frontend\src\components\config\TranscodeForm.vue
       #2245            🟣  Added accessibility attributes to more layout placeholders
     ..\..\Git\GithubManager\ff-intelligent-neo\frontend\src\i18n\locales\zh-CN.ts
       #2246            🔵  Searched for FFmpeg status translation keys
     ..\..\Git\GithubManager\ff-intelligent-neo\frontend\src\components\config\TranscodeForm.vue
       #2247            🔵  Verified no empty divs remain in TranscodeForm
     ..\..\Git\GithubManager\ff-intelligent-neo\frontend\src\i18n\locales\zh-CN.ts
       #2248            🔵  Reviewed FFmpeg status translations in locale files
     ..\..\Git\GithubManager\ff-intelligent-neo\frontend\src\i18n\locales\en.ts
       #2249            🟣  Added ffmpegChecking translation to English locale
     ..\..\Git\GithubManager\ff-intelligent-neo\frontend\src\i18n\locales\zh-CN.ts
       #2250            🟣  Added ffmpegChecking translation to Chinese locale
     ..\..\Git\GithubManager\ff-intelligent-neo\frontend\src\router.ts
       #2251            🔵  Verified router configuration after catch-all route addition
     ..\..\Git\GithubManager\ff-intelligent-neo\frontend\src\components\layout\AppNavbar.vue
       #2252  10:25 PM  🔵  Verified AppNavbar FFmpeg status refactoring complete
     ..\..\Git\GithubManager\ff-intelligent-neo\frontend\src\components\common\ComboInput.vue
       #2253            🔵  Verified ComboInput Escape key handler
     ..\..\Git\GithubManager\ff-intelligent-neo\frontend\src\components\config\TranscodeForm.vue
       #2254            🔵  Verified accessibility attributes in TranscodeForm
     General
       #2260  10:30 PM  🔵  Task 7 marked as completed
```

### 📝 Commit Message

```
feat: v2.1.1 预览性能与交互体验优化

Phase 1 - 预览性能:
- 合并 validate+build 为单次 IPC 调用 (preview_command API)
- 预览模式跳过水印文件存在性检查
- 修复竞态条件 (单调递增 requestId)
- 防抖调整为 500ms 并增加 in-flight 守卫
- 拖拽排序使用唯一 ID 作为 key

Phase 2 - UX 可靠性:
- 错误提示统一为 DaisyUI Alert (3s 自动关闭, i18n)
- 危险操作改用 DaisyUI Modal 确认 (删除/清空/全部停止)
- 复制命令增加"已复制"反馈及剪贴板降级方案
- FFmpeg 下载改为事件驱动, 移除 5s 超时

Phase 3 - 后端响应:
- add_tasks 探测文件改为异步后台线程
- validate_config 返回结构化错误 [{param, message}]

Phase 4 - 代码质量:
- Bridge 事件增加运行时类型守卫
- 修复浮动 Promise (补充 .catch())
- 移除所有 console.log
- 硬编码文案补全 i18n 翻译

Phase 5 - 细节打磨:
- 新增 404 兜底路由重定向至首页
- ComboInput 支持 Escape 关闭下拉
- FFmpeg 状态徽章初始为未知(灰色), 消除红色闪烁
- 空布局节点添加 aria-hidden
```

### 🚀 Release Notes

```
## v2.1.1 - 预览性能与交互体验全面优化

### ✨ 新增
- 命令预览改为单次请求生成，响应更迅速
- 操作错误提示统一为自动消失的提醒条，支持中英文
- 危险操作（删除、清空、全部停止）增加二次确认弹窗
- 复制命令后显示"已复制"反馈
- 无效路径自动重定向至首页
- 下拉选择框支持 Escape 键关闭

### 🐛 修复
- 修复快速切换参数时预览结果错乱的问题
- 修复 FFmpeg 下载可能因超时失败的问题
- 修复文件列表拖拽排序后显示异常
- 修复 FFmpeg 状态检测时徽章短暂闪红的问题

### ⚡ 优化
- 预览防抖策略调整，减少不必要的计算
- 添加任务时文件探测改为后台处理，不再阻塞界面
- 参数校验失败时精确提示出错字段及原因
- 全面补全中英文翻译，消除硬编码文案
```

## 修复

fix1：视频编码器copy和none不能选被冻结了

fix2：@presets\default_presets.json 格式过时了，而且h264那几个的参数也不符合推荐的参数

feat：前端-配置页-编码配置-分辨率应该提供一些常用的横竖屏分辨率预设可供选择

fix3：视频和音频编码器的自定义输入了一个字符之后就不见了，应该是选择自定义就一直显示，选了其他才消失

```
  Changes Made

  fix1: EncoderSelect.vue -- Added special case in isSupported() (line 65) so "copy" and "none" always return true,
  bypassing hardware detection which correctly excludes non-real encoders.

  fix2: default_presets.json -- Updated all 7 presets:
  - H.264/H.265 now use CRF mode (crf=20 / crf=22, preset=medium, pixel_format=yuv420p) instead of bitrate
  - Added all Phase 3.5 quality fields (quality_mode, quality_value, preset, pixel_format, max_bitrate, bufsize)
  - Added Phase 3 filter fields (audio_normalize, target_loudness, true_peak, lra, aspect_convert, target_resolution,
  bg_image_path)
  - Fixed "Extract Audio (WAV)": audio_codec changed from aac to pcm_s16le

  feat: TranscodeForm.vue -- Added resolution preset dropdown above the W/H number inputs with 9 common presets: 4K, 2K,
   1080p, 720p, 480p, 360p (horizontal), 1080x1920, 720x1280 (vertical), 1080x1080 (square). Selecting a preset fills
  both W and H fields; manual edits show "custom" state in dropdown.

  Manual Test Checklist

  1. Encoder select: verify "Copy (no re-encode)" and "No Video" / "No Audio" are selectable (not grayed out)
  2. Presets: load "MP4 H.264" preset, verify quality_mode=crf, quality_value=20, preset=medium appear
  3. Presets: load "Extract Audio (WAV)", verify audio_codec=pcm_s16le
  4. Resolution: in transcode form, verify preset dropdown shows 9 options; selecting one fills W/H inputs; editing W/H
  manually shows custom state
  逻辑：modelValue === ''（刚选了"其他"还没输入）或
  isCustomMode（已输入自定义名称且不是预设编码器）时显示输入框。选择预设编码器后 isCustomMode=false 且 modelValue
  不为空，输入框隐藏。
```

### CC-Mem

    Legend: session-request | 🔴 bugfix | 🟣 feature | 🔄 refactor | ✅ change | 🔵 discovery | ⚖️ decision   
       #2296            🟣  Resolution presets constant array added to TranscodeForm.vue
       #2297            🟣  Resolution preset dropdown added to TranscodeForm.vue template above manual number inputs
     presets/default_presets.json
       #2298  11:25 PM  🔵  default_presets.json validation confirms Phase 3.5 quality parameters correctly set
     ..\..\Git\GithubManager\ff-intelligent-neo\frontend\src\components\config\EncoderSelect.vue
       #2299  11:30 PM  🔴  Fixed encoder custom input field disappearing on first character typed
     General
       #2300            🔴  Build verification passed for encoder custom input fix

### 📝 Commit Message

```
fix(encode): 修复编码选项异常与预设配置

- 修复"直通"和"禁用"编码器因硬件检测被错误冻结的问题
- 修复自定义编码器输入框输入首字符后自动隐藏的逻辑缺陷
- 更新默认预设：H.264/H.265 切换为 CRF 模式，补充质量与滤镜字段
- 修正"提取音频(WAV)"预设的音频编码器配置
- 新增分辨率预设下拉菜单（含横竖屏等 9 种规格），支持手动输入回退
```

### 🚀 Release Notes

```
## 2026-04-25 - 编码配置体验优化与预设升级

### ✨ 新增
- 编码配置新增常用分辨率快捷选项，涵盖 4K、1080p 等横竖屏及方形共 9 种规格，一键填充宽高

### 🐛 修复
- 修复"直通"和"无视频/无音频"编码选项被错误置灰无法选择的问题
- 修复自定义编码器输入框在输入时突然消失的问题
- 修复内置 H.264/H.265 预设参数不符合推荐标准的问题（已升级为质量优先模式）
- 修复"提取音频 (WAV)"预设无法正确输出 WAV 格式的问题
```