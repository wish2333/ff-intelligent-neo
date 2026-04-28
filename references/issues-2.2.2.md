##   Implementation Complete

  Phase 1: Backend CRITICAL + HIGH Safety Fixes (8 fixes)

  - C-3: logging.py - replaced 2x except Exception: pass with stderr warnings
  - H-3: main.py - added _init_lock = threading.Lock() for lazy init
  - H-11: Deleted core/batch_runner.py (309 lines dead code)
  - H-14: main.py - replaced 0x08000000 with subprocess.CREATE_NO_WINDOW
  - H-15: main.py - replaced get_ffmpeg_path().replace(...) with get_ffprobe_path()
  - C-1: models.py - added per-task threading.Lock, append_log(), set_progress(); updated ffmpeg_runner.py and
    task_runner.py to use thread-safe methods
  - H-12: task_runner.py - wrapped concat file creation in try/except for cleanup on submit failure
  - H-13: ffmpeg_runner.py - added _close_pipe() helper, called after reader thread join

  Phase 2: Backend Security Fixes (5 fixes)

  - C-2: auto_editor_api.py - added SHA-256 verification after download
  - H-7: command_builder.py - sanitized stem with Path.stem.name + output dir traversal check
  - H-10: task_runner.py - added _escape_concat_path() for FFmpeg concat demuxer
  - M-1: task_queue.py - atomic write with temp file + os.replace()
  - H-6: auto_editor_api.py + models.py - persisted params to TaskConfig.auto_editor_params for crash recovery

  Phase 3: Frontend Memory Leak Fixes (2 fixes)

  - F-C1: useCommandPreview.ts - added onScopeDispose cleanup
  - F-H1: 5 Vue components - stored timer IDs + added onUnmounted cleanup

  Phase 4: Frontend Type Safety (4 fixes)

  - F-H3: usePresets.ts - 3x catch (e: any) changed to catch (e: unknown)
  - F-H5: useTaskQueue.ts - queue_changed event now validates each field with typeof
  - F-H6: useTheme.ts - replaced as ThemeValue cast with union check
  - F-H10: useGlobalConfig.ts - spread defaults in loadFromTaskConfig() to prevent stale fields

  Phase 5: Cross-cutting (3 fixes)

  - F-H8/H9: Created utils/logger.ts (dev-only logging); replaced 17 console.error calls
  - F-M13: bridge.ts - added withTimeout() with 30s default
  - M-8: Created core/events.py + utils/events.ts; replaced all bare event strings across backend (3 files) and frontend
      (6 files)

  New Files

  - frontend/src/utils/logger.ts
  - core/events.py
  - frontend/src/utils/events.ts

  Deleted Files

  - core/batch_runner.py

  Manual Testing Checklist

  1. Start the app, verify all pages load
  2. Navigate between pages rapidly (timer cleanup)
  3. Add/start/stop FFmpeg tasks (thread safety)
  4. Settings save/load (no console.error)
  5. Task queue summary updates (event validation)
  6. Theme/language switching (cast validation)

- 现在打开队列页会无限转圈（已解决）
- auto-editor自动检测错误，命令构建未能预览（已解决）
- 把“重置全部”放到预设模块的预设选项栏的右边（已修改）

### Apr 29, 2026

3910 12:47a 🔴 Queue page infinite loading issue reported
3911 12:48a 🔵 Event emission system uses self._emit pattern
3912 " 🔵 Frontend event listeners registered in multiple components
3913 " 🔵 Task queue listens for four key events
3914 12:50a 🔵 Task queue triggers full refresh on completion state changes
3915 " 🔵 TaskQueuePage uses Promise.all for initial data loading
3916 " 🔵 TaskQueuePage loading state controlled by isReady flag
3917 " 🔵 Loading spinner controlled by isReady ref
3918 " 🔵 Backend task queue emits summary on changes
3919 12:51a 🔵 Task queue summary computed under lock protection
3920 " 🔵 Frontend fetchSummary calls backend get_queue_summary
3921 " 🔵 Task queue uses callback pattern for change notifications
3922 " 🔵 Frontend uses pywebvue event system with automatic cleanup
3923 12:53a 🔵 fetchSummary lacks error handling and timeout protection
3924 12:54a 🔵 useTaskQueue composable exports complete task management API
3925 12:55a 🔵 Bridge timeout applied after await instead of to the call itself
3926 1:09a 🔵 Code audit review initiated for frontend and backend components
3927 " 🔵 TaskQueuePage component implements loading spinner with drag-drop file upload
3928 " 🔵 Backend API exposes 47 endpoints via @expose decorator
3929 " 🔵 Backend API exposes task queue endpoints with exception handling
3930 " 🔵 Backend queue endpoints implement consistent error handling pattern
3931 " 🔵 Backend implements thread-safe lazy initialization for queue and runner
3932 1:12a 🔵 Backend architecture uses pywebview Bridge pattern with event-driven communication
3933 1:14a 🔄 useTaskQueue composable refactored to use structured logging and event constants
3934 " 🔴 Bridge call timeout implemented to prevent indefinite hangs
3935 " 🔄 Backend main.py refactored for thread safety and code quality
3936 1:15a 🔴 task_runner.py fixed Windows path escaping and added thread safety
3937 1:16a 🔄 task_runner.py centralized log handling through task.append_log method
3938 1:17a 🔴 task_queue.py implemented atomic write to prevent queue state corruption
3939 1:27a 🔄 Use constant for auto editor version changed event
3940 1:29a 🔄 Use constant for task progress event
3941 1:36a 🔄 Standardize error logging in useSettings composable
3942 1:37a 🔵 Backend and frontend validation successful after refactoring
3943 " 🔴 Fix stale config fields in loadFromTaskConfig
3944 1:38a 🔴 Added thread-safety to Task model
3945 " 🔴 Added download integrity verification and restart recovery for auto-editor tasks
3946 1:43a 🔴 Changed initialization lock to reentrant lock
3947 " 🔴 Fixed undefined function reference in save_settings
3948 " 🔴 Fixed timeout wrapper in bridge call function
3949 2:04a 🔵 Settings page "Reset All" button relocation to preset selector
3950 " 🔵 Reset All button pattern exists in CommandConfigPage but not in SettingsPage
3951 " 🟣 PresetSelector component enhanced with dropdown-actions slot

```
  #3952  2:30 AM  🔵  macOS ffprobe detection uses platform-specific Homebrew paths  
..\..\Git\GithubManager\ff-intelligent-neo\core\models.py
  #3953           🔵  AppSettings model stores separate ffprobe_path configuration  
..\..\Git\GithubManager\ff-intelligent-neo\main.py
  #3954  2:31 AM  🔵  API endpoints depend on ffprobe for media analysis  
..\..\Git\GithubManager\ff-intelligent-neo\frontend\src\components\settings\FFmpegSetup.vue
  #3955           🔵  Frontend FFmpegSetup component manages binary configuration UI  
  #3956           🔵  Frontend provides platform-specific FFmpeg installation guidance  
..\..\Git\GithubManager\ff-intelligent-neo\core\ffmpeg_setup.py
  #3957           🔴  Fixed macOS FFmpeg path detection to check both Homebrew locations  
  #3958           🔴  Removed unused machine architecture detection after Homebrew path fix  
  #3959           🔵  Platform module import now unused after architecture detection removal  
  #3960           🔄  Removed unused platform module import from ffmpeg_setup.py  
General
  #3961  2:37 AM  🔴  Mac frontend error on auto-editing and custom pages  
  #3962           🔵  Frontend page files located  
  #3963           🔵  Auto-editor codebase structure mapped  
frontend/src/router.ts
  #3964           🔵  Router configuration identifies error-prone pages  
frontend/src/pages/AutoCutPage.vue
  #3965           🔵  AutoCutPage.vue component structure  
General
  #3966  2:38 AM  🔵  Vue SFC parsing limitation encountered  
  #3967           🔵  AutoCutPage component uses icon rendering with dynamic attributes  
frontend/src/pages/CustomCommandPage.vue
  #3968           🔵  CustomCommandPage.vue component structure  
General
  #3969           🔵  DOM element creation patterns searched  
frontend/src/components/config/CommandPreview.vue
  #3970           🔵  Only one document.createElement call found in frontend  
  #3971           🔵  CommandPreview createElement uses valid element name  
General
  #3972           🔵  Dynamic component patterns absent from codebase  
  #3973           🔵  Extensive SVG usage found across frontend components  
  #3974           🔵  No string concatenation in DOM creation patterns  
  #3975           🔵  No v-html usage found in frontend codebase  
  #3976  2:39 AM  🔵  Lazy loading and async imports identified in router  
frontend/src/pages/AutoCutPage.vue
  #3977           🔵  AutoCutPage template structure examined  
General
  #3978           🔵  CustomCommandPage template spans 245 lines  
frontend/src/pages/CustomCommandPage.vue
  #3979           🔵  CustomCommandPage template structure with inline SVG  
General
  #3980  2:40 AM  🔵  SVG attributes properly formatted in static templates  
frontend/src/utils/events.ts
  #3981           🔵  Event constants and dynamic component patterns examined  
General
  #3982           🔵  No manual render functions or h() calls found  
  #3983           🔵  CustomCommandPage probe data usage patterns  
  #3984           🔵  CustomCommandPage textarea v-model binding  
frontend/src/components/config/CommandPreview.vue
  #3985  2:41 AM  🔵  Agent investigation identifies InvalidCharacterError sources  
General
  #3986           🔵  Only one createElement call confirmed in codebase  
frontend/src/composables/useTheme.ts
  #3987           🔵  No dynamic component rendering found; single setAttribute call confirmed  
General
  #3988           🔵  No dangerous HTML manipulation methods found  
  #3989           🔵  SVG elements and path attributes verified as properly formatted  
  #3990           🔵  No dynamic HTML rendering or text node manipulation found  
https://github.com/nextcloud/richdocuments/issues/5490
  #3991  3:23 AM  🔵  Vue.js InvalidCharacterError with @canAssign in Safari/Firefox  
General
  #3992  3:33 AM  🔴  Mac-specific frontend error in auto-edit and custom pages  
  #3993  3:34 AM  🔵  InvalidCharacterError investigation initiated on macOS builds  
frontend/src/components/config/CommandPreview.vue
  #3994           🔵  Located source files for macOS InvalidCharacterError  
frontend/src/pages/AutoCutPage.vue
  #3995           🔵  AutoCutPage and CustomCommandPage file structure identified  
  #3996  3:35 AM  🔵  File size analysis for InvalidCharacterError investigation  
frontend/src/components/config/CommandPreview.vue
  #3997           🔵  Historical investigation reveals @canAssign InvalidCharacterError root cause  
..\..\Git\GithubManager\ff-intelligent-neo\frontend\src\main.ts
  #3998           ✅  Added Vue global error handler to main.ts  
frontend/src/pages/AutoCutPage.vue
  #3999           🔵  AutoCutPage.vue source code examined for InvalidCharacterError  
frontend/src/pages/CustomCommandPage.vue
  #4000           🔵  CustomCommandPage.vue source code examined  
frontend/src/components/config/CommandPreview.vue
  #4001  3:36 AM  🔵  CommandPreview.vue source code examined; createElement call confirmed safe  
frontend/src/components/auto-cut/BasicTab.vue
  #4002           🔵  BasicTab and AdvancedTab components examined; no DOM manipulation found  
frontend/src/components/common/FileDropInput.vue
  #4003  3:37 AM  🔵  FileDropInput.vue component examined; no DOM element creation issues found  
frontend/src/composables/useAutoEditor.ts
  #4004           🔵  useAutoEditor composable examined; no DOM manipulation in first 150 lines  
frontend/src/components/common/FileDropInput.vue
  #4005           🔵  FileDropInput.vue additional lines examined; file validation logic reviewed  
  #4006           🔵  FileDropInput.vue template section examined; drag event handlers confirmed  
  #4007  3:38 AM  🔵  FileDropInput.vue template class bindings examined; complex conditional styling found  
main.ts
  #4008           🔴  Vue InvalidCharacterError fixed in AutoCutPage component  
frontend/src/main.ts
  #4009  3:39 AM  🔵  Vue error handler configured in main.ts  
main.ts
  #4010  3:43 AM  🔴  Fixed setAttribute call causing display race condition  
src/main.ts
  #4011  3:45 AM  🔵  Vue.js setAttribute Error with Invalid Attribute Name  
frontend/src/main.ts
  #4012  3:46 AM  🔵  Debug Instrumentation Added to Track Invalid Attribute Name  
src/main.ts
  #4013  3:48 AM  🔵  Vue.js invalid attribute error on Tailwind-styled DIV  
frontend/src/components/common/FileDropInput.vue
  #4014           🔵  FileDropInput component uses Vue 3 Composition API with defineProps  
  #4015           🔵  Invalid empty string attribute found in FileDropInput template  
  #4016  3:50 AM  🔴  Removed invalid empty string attribute from FileDropInput template  
  #4017           🔴  FileDropInput.vue fix verified - empty string attribute removed  
  #4018           🔴  FileDropInput.vue invalid attribute bug resolved and verified  
  #4019           🔵  Empty string attribute confirmed at line 243 in FileDropInput.vue  
  #4020           🔴  Removed invalid empty string attribute from FileDropInput.vue template  
frontend/src/main.ts
  #4021           🔄  Removed debug instrumentation from main.ts after bug fix  
app.spec
  #4022  3:54 AM  🔵  Build configuration file discovered  
pyproject.toml
  #4023           🔵  Python project build system identified  
scripts/pre_build.py
  #4024           🔵  Build scripts directory structure found  
build/app/ff-intelligent-neo.exe
  #4025           🔵  Project architecture revealed as Python desktop app with Vue frontend  
pyproject.toml
  #4026           🔵  Project identified as FFmpeg batch processing desktop tool  
frontend/vite.config.ts
  #4027           🔵  Frontend build configuration uses Vite with Vue and Tailwind  
frontend/package.json
  #4028           🔵  Frontend build process and pre-build automation identified  
.gitignore
  #4029           🔵  Build artifacts and generated files identified in .gitignore  
app.spec
  #4030  3:55 AM  🔵  PyInstaller spec file structure revealed  
build.py
  #4031           🔵  Comprehensive cross-platform build script discovered  
dist/
  #4032           🔵  Current build output format is Windows x64 .7z archives  
app.spec
  #4033           🔵  Existing cross-platform infrastructure identified  
dist/ff-intelligent-neo-use/
  #4034           🔵  Current PyInstaller onedir build structure confirmed  
  #4035  3:56 AM  🔵  Frontend assets not visible at PyInstaller output root level  
app.spec
  #4036           🔵  PyInstaller data collection uses COLLECT with binaries and datas  
  #4037           🔵  Frontend assets are bundled into PyInstaller via datas configuration  
  #4038  3:57 AM  🔵  Build system architecture fully documented by exploration agent  
General
  #4039           🔵  No macOS app bundle assets exist in project  
C:\Users\10411\.claude\plans\glowing-swimming-ocean.md
  #4040  3:58 AM  ⚖️  Implementation plan created for macOS .app bundle packaging  
  #4041           ⚖️  Plan approved and exiting plan mode for implementation  
app.spec
  #4042           🟣  Version reading helper added to app.spec  
  #4043           🟣  macOS .app bundle BUNDLE block added to app.spec  
build.py
  #4044           🟣  macOS .app packaging implementation completed  
app.spec
  #4045           🟣  macOS .app packaging implementation verified  
frontend/src/pages/AutoCutPage.vue
  #4046  4:02 AM  🔵  Auto-editor status briefly shows "not configured" error on macOS  
frontend/src/composables/useAutoEditor.ts
  #4047           🔵  Root cause identified: autoEditorStatus initialization race condition  
  #4048           🔵  Initializing flag exists but not used in AutoCutPage  
frontend/src/pages/AutoCutPage.vue
  #4049  4:03 AM  🔴  Fixed auto-editor status flash by adding initialization check  
frontend/src/composables/useAutoEditor.ts
  #4050           🔵  Alert system architecture in useAutoEditor composable  
frontend/src/pages/AutoCutPage.vue
  #4051           🔴  Fixed auto-editor initialization race condition on macOS  
main.py
  #4052           🔵  Error message "auto-editor path not config" originates from frontend  
frontend/src/i18n/locales/zh-CN.ts
  #4053           🔵  Chinese translation confirms "notConfigured" error text  
core/auto_editor_api.py
  #4054           🔵  Backend returns "Auto-editor path not configured" error when path empty  
frontend/src/composables/useAutoEditor.ts
  #4055           🔵  useAutoEditor has watch with immediate:true triggering initial status fetch  
  #4056           🔵  Immediate watch triggers updatePreview on component mount  
  #4057  4:04 AM  🔵  Preview update debounced by 300ms with immediate execution  
  #4058           🔴  Fixed auto-editor initialization race condition by checking initializing flag  
  #4059  4:09 AM  🔵  Alert flashing mechanism in auto editor preview  
  #4060           🔵  Race condition between immediate watch and initialization flag  
  #4061           🔴  Fixed red text flashing by using availability check instead of initialization flag  
  #4062           🔴  Removed immediate watch trigger to prevent premature preview updates
```

### 📝 Commit Message

```
fix(core): 全面修复安全与稳定性隐患

- 后端：修复线程安全问题，清理死代码，增加下载校验与路径防穿越
- 后端：引入原子写入与事件常量化，提升进程间通信可靠性
- 前端：修复多组件内存泄漏与定时器未清理问题
- 前端：强化类型检查，替换不安全的类型断言与隐式 any
- 修复队列页无限加载与 auto-editor 预览失败问题
- UI：调整"重置全部"按钮位置至预设选项栏右侧
- 修复：移除了FileDropInput.vue组件中click事件处理程序后的无效引号
```

### 🚀 Release Notes

```
## 2026-04-29 - 应用稳定性与安全性全面加固

### 🐛 修复
- 修复进入任务队列页面时出现的无限加载问题
- 修复 auto-editor 自动检测报错及命令预览无法正常显示的问题
- 修复快速切换页面时可能导致的界面卡顿与内存占用异常
- 移除了FileDropInput.vue组件中click事件处理程序后的无效引号
- 修复初始化时错误提示显示问题

### ⚡ 优化
- 全面提升后台任务处理的安全性与异常容错能力，避免任务意外中断
- 优化前端组件状态管理，提升页面响应速度与运行稳定性
- 调整界面布局：将"重置全部"按钮移动至预设选项栏右侧，操作更符合直觉
- 添加macOS应用打包配置和版本读取功能
```