## 问题1

- 优化命令预览区域：进入新的界面是命令预览首先显示的是“在上方配置转码设置以查看FFmpeg命令”小字，不需要，直接显示ffmpeg
作为占位符即可，这样子后面命令更新起来更自然不会闪一下。
- 此外检测成功的“0个错误，0个警告”和错误警告的高度不相同，首先统一高度，然后预留一行的位置空白，这样更新好之后提示的出
现不会导致界面位置变动。
- 修改编码配置的操作有时候会导致整个界面闪动一下，影响用户体验

  Changes in CommandPreview.vue

    1. Placeholder text (line 79): Replaced "在上方配置转码设置以查看FFmpeg命令" with a static ffmpeg in dimmed monospace font. When the real command arrives, it naturally replaces this — no jarring text swap.
    2. Validation area layout (line 88): Added min-h-[2.25rem] wrapper div that always reserves space for validation results. Whether showing errors/warnings or "0 errors, 0 warnings" or nothing, the container height stays consistent —   no layout shift when validation results appear.
    3. Flicker fix (lines 77-84): Instead of replacing the command text with a spinner + "Updating..." during validation, the existing command text stays visible while a small spinner appears in the top-right corner. The command only  updates when the new result arrives, eliminating the flash.

  Manual Testing Checklist

  - Open the command config page — verify ffmpeg placeholder shows in dimmed text (not the old Chinese placeholder)
  - Change a codec setting — verify the old command stays visible with a small spinner in the corner, no flash
  - Verify that when validation completes with errors/warnings, they appear without shifting the page layout
  - Verify that the success message "0 errors, 0 warnings" occupies the same reserved space as error/warning message would

## 问题2

- 顶部导航栏居中不太美观，因为左边和右边宽度不一致，干脆把导航路由栏从居中变成放到左边FF NEO的右边跟着吧

导航栏从 navbar-center 移到了 navbar-start，紧跟 "FF Neo" 右侧，右侧的语言/主题/FFmpeg 状态图标保持在 navbar-end 对齐到右边。

## 问题3

- 编码器MAC兼容性
  - MAC端隐藏 nvenc/amf/qsv 等硬件编码器以及不支持的av1编码器，新增支持h264_videotoolbox hevc_videotoolbox这两个硬件编码器（这两个编码器只能使用-b:v xxxx指定码率和-q:v 65指定质量）
- 配置页-编码配置
  - 分辨率/质量模式选项栏添加默认选项（或者选择其他选项之后把默认显示的选项可选）以清除选择并取消传参

```
  Changes Summary

  Feature 1: MAC Encoder Compatibility

  - frontend/src/types/config.ts: Added "apple" to hardwareType union, "q" to qualityMode
  - frontend/src/data/encoders.ts: Added h264_videotoolbox and hevc_videotoolbox encoders with hardwareType: "apple",
  qualityMode: "q"
  - frontend/src/components/config/EncoderSelect.vue: Added platform prop, filters out NVIDIA/AMD/Intel hardware
  encoders and AV1 encoders on macOS
  - frontend/src/components/config/TranscodeForm.vue: Accepts and passes platform prop to both EncoderSelect instances
  - frontend/src/pages/CommandConfigPage.vue: Fetches appInfo via useSettings(), passes platform to TranscodeForm
  - core/command_builder.py: Added h264_videotoolbox/hevc_videotoolbox to VALID_VIDEO_CODECS, "q" to VALID_QUALITY_MODES
  - frontend/src/i18n/locales/en.ts + zh-CN.ts: Added q quality mode label

  Feature 2: Default Options for Resolution/Quality Mode

  - Resolution dropdown: Removed disabled from placeholder option, selecting it now clears config.resolution
  - Quality mode dropdown: Replaced v-model with :value + @change, selecting placeholder now clears both quality_mode
  and quality_value

  Manual Test Items

  1. On macOS: Encoder list should show Apple videotoolbox, hide NVENC/AMF/QSV/AV1
  2. On Windows: No visible change
  3. Select resolution preset -> select default placeholder -> resolution clears
  4. Select quality mode -> select default placeholder -> quality_mode + quality_value clear
  5. Select h264_videotoolbox -> auto-fills quality mode "q" with value 65
  6. Command preview shows -q:v 65 for videotoolbox encoders
```

> Windows应该也隐藏mac相关编码器。而且现在布局又乱了，正确的应该是：
> ```
> VC----Resolution----AC
> QM----Framerate----AB
> QV----VB----OutputFormat
> EP----MB
> PF
> ```

- 默认把自定义编码器的输入框显示出来吧，输入了内容就自动切换编码器选项到自定义
- 质量值的输入栏也是这样，不过输入后不用自动切换模式，没选模式就不注入参数
- 现在Win端还是没有隐藏mac的编码器啊
  - 现在 fetchAppInfo() 会在 CommandConfigPage 挂载时调用，platform 会拿到 "win32" 值，EncoderSelect 就能正确过滤掉 Apple
      编码器了。

## CC-Mem

     Apr 26, 2026
    
     ..\..\Git\GithubManager\ff-intelligent-neo\frontend\src\components\config\TranscodeForm.vue
       #2488  1:34 PM  🔵  TranscodeForm reactive declarations precisely located
     ..\..\Git\GithubManager\ff-intelligent-neo\frontend\src\composables\useGlobalConfig.ts
       #2489           🔵  Global config uses pure Vue reactivity without custom events
     ..\..\Git\GithubManager\ff-intelligent-neo\frontend\src\bridge.ts
       #2490           🔵  useCommandPreview composable used across multiple pages
       #2491           🔵  Bridge layer provides pywebview IPC communication
     ..\..\Git\GithubManager\ff-intelligent-neo\frontend\src\components\config\CommandPreview.vue
       #2492  1:35 PM  🔵  Complete frontend architecture analysis completed
     ..\..\Git\GithubManager\ff-intelligent-neo\frontend\src\composables\useCommandPreview.ts
       #2493           🔵  Implementation phase initiated for UI improvements
       #2495           🔵  Implementation planning phase completed
     ..\..\Git\GithubManager\ff-intelligent-neo\frontend\src\components\config\CommandPreview.vue
       #2496           🔵  Codebase analysis finalized, implementation pending
     ..\..\Git\GithubManager\ff-intelligent-neo\frontend\src\composables\useCommandPreview.ts
       #2497           🔵  Complete implementation targets identified with line numbers
     General
       #2498           🔵  CommandPreview component usage scope confirmed across 4 pages
     ..\..\Git\GithubManager\ff-intelligent-neo\frontend\src\components\config\TranscodeForm.vue
       #2499           🔵  TranscodeForm reactive patterns fully documented with line numbers
     ..\..\Git\GithubManager\ff-intelligent-neo\frontend\src\pages\CommandConfigPage.vue
       #2500           🔵  CommandConfigPage reactive data flow fully documented
     ..\..\Git\GithubManager\ff-intelligent-neo\frontend\src\composables\useGlobalConfig.ts
       #2501           🔵  Global config uses module-level reactive singleton pattern
     General
       #2502           🔵  Three implementation tasks created for feature requirements
       #2503  1:36 PM  🔵  Task #1 implementation started: placeholder text replacement
     ..\..\Git\GithubManager\ff-intelligent-neo\frontend\src\components\config\CommandPreview.vue
       #2504           🟣  CommandPreview placeholder text replaced with "ffmpeg"
     General
       #2505           🔵  Task progression: #1 completed, #3 started
     ..\..\Git\GithubManager\ff-intelligent-neo\frontend\src\components\config\CommandPreview.vue
       #2506           🟣  Validation area height standardized with reserved space
     General
       #2507           🔵  Task progression: #3 completed, #2 started
     ..\..\Git\GithubManager\ff-intelligent-neo\frontend\src\components\config\CommandPreview.vue
       #2508  1:37 PM  🔵  CommandPreview.vue verified at 116 lines after modifications
       #2509           🔵  CommandPreview.vue modifications verified in current state
       #2510           🟣  Command display optimized to prevent flash during validation
       #2511           🟣  All three UI improvement tasks completed
     General
       #2512  1:39 PM  🔵  TypeScript validation passed with no errors
     ..\..\Git\GithubManager\ff-intelligent-neo\frontend\src\components\config\CommandPreview.vue
       #2513           🔵  Final CommandPreview.vue state verified with all modifications
     frontend/src/components/config/CommandPreview.vue
       #2514  1:47 PM  ✅  CommandPreview component vertical spacing reduced
     General
       #2515  1:50 PM  ✅  Navigation bar layout changed from centered to left-aligned
     src/components/layout/AppNavbar.vue
       #2516           🔵  FF NEO brand element located in AppNavbar.vue component
       #2517           🔵  AppNavbar.vue structure uses DaisyUI navbar layout with three sections
     references/auto-cut.md
       #2518  2:15 PM  🔵  Project structure exploration initiated for auto-editor CLI integration
     CLAUDE.md
       #2519           🔵  Project structure revealed through documentation analysis
       #2520           🔵  Project build system and toolchain identified
     docs/Structure.md
       #2521           🔵  auto-editor CLI tool already installed in project environment
     references/auto-cut.md
       #2522  2:16 PM  🔵  Project directory structure and auto-editor reference documentation analyzed
     frontend/src/App.vue
       #2523           🔵  Frontend architecture identified as Vue.js with pywebvue bridge
     pywebvue/bridge.py
       #2524           🔵  Core backend modules and frontend component structure identified
     frontend/src/router.ts
       #2525           🔵  Application routing structure and existing pages catalogued
     core/task_runner.py
       #2526           🔵  Task execution and command building architecture identified
     General
       #2527           🔵  Frontend component organization by domain identified
     frontend/src/composables/useBridge.ts
       #2528           🔵  Vue composables architecture for state management and bridge communication
     General
       #2529  2:17 PM  🔵  Codebase size and complexity measured
     core/models.py
       #2530           🔵  Task state machine and data model architecture defined
     frontend/src/pages/TaskQueuePage.vue
       #2531           🔵  Page component architecture pattern identified
     frontend/src/main.ts
       #2532           🔵  Vue 3 application initialization with standard plugin pattern
     pywebvue/app.py
       #2533           🔵  Pywebvue App class and application entry point structure
     pywebvue/bridge.py
       #2534           🔵  Bridge API pattern and main application entry point identified
     main.py
       #2535           🔵  FFmpegApi main interface architecture with lazy initialization pattern
     references/auto-cut.md
       #2536  2:18 PM  🔵  Project exploration completed - architecture fully mapped
       #2537           🔵  Complete project architecture documented via comprehensive exploration
       #2538  2:42 PM  🔵  CLI feature integration planning for auto-cut
         core/config.py
           #2545  2:51 PM  🔵  Confirmed encoder configuration is frontend-only
         frontend/src/composables/useGlobalConfig.ts
           #2546           🔵  Confirmed no platform detection in backend
         frontend/src/data/encoders.ts
           #2547           🔵  Documented quality mode implementation architecture
         references/auto-cut.md
           #2548           🟣  Auto-cut CLI functionality integrated as new software page
         frontend/src/composables/useSettings.ts
           #2549  2:52 PM  🔵  Confirmed absence of platform detection infrastructure
         frontend/src/data/encoders.ts
           #2550           🔵  Identified Python backend structure and quality mode validation gap
         frontend/src/i18n/locales/en.ts
           #2551           🔵  Mapped quality mode localization and confirmed no default option exists
         frontend/src/data/encoders.ts
           #2552           🔵  Found existing platform detection infrastructure and encoder hardware classification
         frontend/src/components/config/TranscodeForm.vue
           #2553           🔵  Documented quality mode and value separation in configuration
         core/command_builder.py
           #2554           🔵  Found backend quality mode validation and FFmpeg command building logic
         frontend/src/data/encoders.ts
           #2555  2:53 PM  🔵  Completed comprehensive codebase architecture exploration
         frontend/src/components/config/TranscodeForm.vue
           #2556           🔵  Documented encoding configuration page architecture and value flow
         frontend/src/data/encoders.ts
           #2557           🔵  Read complete implementation of encoder system and quality mode configuration
         core/app_info.py
           #2558           🔵  Found platform detection infrastructure and supportedEncoders state management
         frontend/src/pages/SettingsPage.vue
           #2559  2:54 PM  🔵  Found existing platform detection usage in frontend
         core/command_builder.py
           #2560  2:56 PM  🔵  Documented backend quality mode parameter building and validation logic
         frontend/src/composables/useSettings.ts
           #2561           🔵  Documented TypeScript type definitions for app info and encoder configuration
         frontend/src/data/encoders.ts
           #2562  2:58 PM  ⚖️  Entered plan mode for MAC encoder compatibility and quality mode default option features
         General
           #2563           🔵  Confirmed no macOS detection utility exists in frontend
         frontend/src/i18n/locales/en.ts
           #2564           🔵  Documented i18n locale structure for quality mode labels
         frontend/src/pages/CommandConfigPage.vue
           #2565           🔵  Documented hardware encoder detection flow in CommandConfigPage
         General
           #2566  2:59 PM  ⚖️  Created implementation plan for MAC encoder compatibility and default option features
           #2567  3:01 PM  ⚖️  Exited plan mode with approved implementation plan
           #2568  3:02 PM  🟣  Started implementation: Adding i18n translations for quality mode "q"
           #2569           🟣  Created task queue for implementation with 7 tasks covering all plan changes
         frontend/src/types/config.ts
           #2570           🟣  Extended TypeScript type definitions for Apple hardware and quality mode "q"
         frontend/src/data/encoders.ts
           #2571           🟣  Added Apple videotoolbox encoders to VIDEO_ENCODERS registry
         frontend/src/components/config/EncoderSelect.vue
           #2572           🟣  Added platform prop to EncoderSelect component
           #2573           🟣  Implemented platform-based encoder filtering for macOS
           #2574  3:03 PM  🟣  Connected platform filtering to encoder selection
           #2575           🟣  Fixed isPresetEncoder to use platform-filtered encoder list
         frontend/src/pages/CommandConfigPage.vue
           #2576           🟣  Started platform prop passing implementation in CommandConfigPage
           #2577           🟣  Initialized appInfo access in CommandConfigPage
           #2578           🟣  Passed platform prop from CommandConfigPage to TranscodeForm
         frontend/src/components/config/TranscodeForm.vue
           #2579           🟣  Added platform prop to TranscodeForm component
           #2580           🟣  Passed platform prop to video EncoderSelect in TranscodeForm
           #2581           🟣  Completed platform prop passing to audio EncoderSelect
         General
           #2582           🟣  Task status updates: Platform prop passing completed, backend validation started
         core/command_builder.py
           #2583  3:05 PM  🟣  Added videotoolbox codecs to backend VALID_VIDEO_CODECS
         ..\..\Git\GithubManager\ff-intelligent-neo\frontend\src\components\config\TranscodeForm.vue
           #2584  3:13 PM  🔵  TranscodeForm.vue layout structure examined
         ..\..\Git\GithubManager\ff-intelligent-neo\frontend\src\components\config\EncoderSelect.vue
           #2585           🔴  EncoderSelect platform filtering extended to hide Apple encoders on non-macOS
         ..\..\Git\GithubManager\ff-intelligent-neo\frontend\src\components\config\TranscodeForm.vue
           #2586           🟣  Added "q" quality mode option to TranscodeForm
           #2587  3:14 PM  🔄  TranscodeForm conditional rendering changed from v-if to v-show
         General
           #2588           🔵  Frontend build verification successful after platform filtering and v-show changes
           #2589  3:17 PM  🔵  Quality mode parameter implementation uses dynamic flag generation
           #2590  3:21 PM  🟣  Custom encoder input field now visible by default
           #2591  3:22 PM  🟣  Quality value input field now shows without requiring mode selection
           #2592  3:24 PM  🔵  Hardware encoder detection flow on frontend
         ..\..\Git\GithubManager\ff-intelligent-neo\frontend\src\pages\CommandConfigPage.vue
           #2593           ✅  Added fetchAppInfo to CommandConfigPage imports
           #2594           ✅  Added fetchAppInfo call before hardware encoder detection General
           #2595  3:31 PM  ✅  Task 4 marked as completed
         ..\..\Git\GithubManager\ff-intelligent-neo\docs
           #2596           🔵  Project documentation structure identified
         core/command_builder.py
           #2597  3:54 PM  🔵  Quality range validation error located
           #2598           🔵  Quality value validation bounds incorrect in command builder
         docs/superpowers/specs/2026-04-26-auto-editor-design.md
           #2599  3:55 PM  🔴  Auto-Editor CLI integration design documented
         General
           #2600  3:57 PM  🔵  Current branch identified as dev-2.1.2

## 📝 Commit Message

```
feat(config): Mac编码器支持与配置界面体验优化

命令预览区域：
- 占位符改为静态 "ffmpeg"，避免命令更新时文字闪烁
- 校验结果区域固定高度，消除出现时的布局偏移
- 校验中保留旧命令并显示角标 spinner，不再替换为加载文案

导航栏：
- 路由导航从居中改为左对齐，紧跟品牌标识右侧

Mac 编码器兼容：
- 新增 h264_videotoolbox / hevc_videotoolbox 硬件编码器
- macOS 隐藏 NVENC/AMF/QSV/AV1，非 macOS 隐藏 Apple 编码器
- 新增 "q" 质量模式，后端同步校验放行

编码配置表单：
- 分辨率/质量模式下拉支持选回默认项以清除对应参数
- 自定义编码器输入框默认展示，输入内容自动切到自定义
- 质量值输入框默认展示，未选模式时不注入参数
- 修正表单网格布局，统一各控件排列顺序
- 条件渲染改用 v-show 避免重复挂载开销
```

## 🚀 Release Notes

```
## 2026-04-26 - Mac 编码器支持与配置体验升级

### ✨ 新增
- 支持 macOS 硬件编码器：H.264 VideoToolbox 和 HEVC VideoToolbox
- 编码配置页新增"自定义编码器"输入框，默认直接展示，输入后自动切换
- 质量值输入框默认可见，灵活按需填写

### ⚡ 优化
- 命令预览区不再闪烁：配置变更时旧命令保持显示，仅出现加载指示
- 校验提示出现不再导致页面跳动，区域高度已固定
- 分辨率和质量模式下拉支持选回默认项以清除设置
- 顶部导航栏调整为左对齐布局，视觉更均衡

### 💥 Breaking Changes
- macOS 下将自动隐藏 NVIDIA/AMD/Intel 硬件编码器及 AV1 编码选项
- 非 macOS 平台不再显示 Apple VideoToolbox 编码器
```