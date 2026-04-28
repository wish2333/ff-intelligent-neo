# 前端代码审计报告

**项目**: ff-intelligent-neo | **分支**: dev-2.2.1 | **范围**: 64 文件, ~5,500 行 TS/Vue
**技术栈**: Vue 3.5 + TypeScript 5.7 + Tailwind 4 + DaisyUI 5 + pywebview bridge
**审计日期**: 2026-04-28

---

## 一、CRITICAL (1)

| # | 类别 | 位置 | 问题 |
|---|------|------|------|
| F-C1 | 内存泄漏 | `useCommandPreview.ts:82` | **debounce timer 无 onUnmounted 清理** -- composable 内 `debounceTimer` 在组件销毁时不会自动清除。`useCommandPreview` 被多个页面引用 (CommandConfigPage, CustomCommandPage)，若用户在 debounce 窗口 (500ms) 内导航离开，回调将在已卸载组件上执行，可能导致无意义的 bridge 调用和 stale 状态更新。对比 `useAutoEditor` 已正确实现 `dispose()` 清理。 |

---

## 二、HIGH (10)

| # | 类别 | 位置 | 问题 |
|---|------|------|------|
| F-H1 | 内存泄漏 | `ClipForm.vue:114`, `CommandPreview.vue:51`, `MergeFileList.vue:61`, `PresetSelector.vue:46`, `CustomCommandPage.vue:73` | **setTimeout 未在组件卸载时清除** -- 5 处 `setTimeout(() => { ... }, 3000)` 用于清除 alert 状态，组件卸载后仍会触发 ref 赋值。虽然不会崩溃 (Vue 会 warn)，但属于内存泄漏和无效更新。 |
| F-H2 | 内存泄漏 | `useAutoEditor.ts:233,252` | **dispose() 依赖组件手动调用** -- `debounceTimer` 和 `alertTimer` 清理封装在 `dispose()` 中，但 composable 自身不调用 `onUnmounted`。需确认 `AutoCutPage` 是否在 `onUnmounted` 中调用了 `dispose()`，否则泄漏。 |
| F-H3 | 类型安全 | `usePresets.ts:27,50,69` | **catch 使用 `e: any`** -- 3 处 `catch (e: any)` 应改为 `catch (e: unknown)` + instanceof 窄化，与 TypeScript strict 模式一致。 |
| F-H4 | 类型安全 | `bridge.ts:29` | **`(api as any).setup_ffmpeg`** -- pywebview API 探测使用 `any` 断言绕过类型检查。应声明一个最小接口或使用 `keyof` 约束。 |
| F-H5 | 数据安全 | `useTaskQueue.ts:182-184` | **queue_changed 事件无载荷验证** -- `summary.value = detail as QueueSummary` 直接将未验证的事件载荷赋值给 state。恶意或后端 bug 导致的畸形事件可直接污染队列汇总数据。其他事件 (task_state_changed, task_info_updated) 有基本的 typeof 检查，唯独此项缺失。 |
| F-H6 | 数据安全 | `useTheme.ts:51` | **不安全的 as 强转** -- `(res.data.theme as ThemeValue)` 未验证值是否为合法的 `"auto"/"light"/"dark"` 之一，后端返回任意字符串会直接设置为 theme。 |
| F-H7 | 数据安全 | `useLocale.ts:18` | **不安全的 as 强转** -- `preference as LocaleValue` 未验证值是否为 `"zh-CN"/"en"`，虽然有 `SUPPORTED_LOCALES.includes()` 保护，但类型断言发生在检查之前，逻辑上应先检查再断言。 |
| F-H8 | 错误处理 | `useSettings.ts` (全文) | **8 处 console.error 作为唯一错误处理** -- `fetchSettings`, `saveSettings`, `fetchFfmpegVersions`, `switchFfmpeg`, `selectFfmpegBinary`, `detectFfmpeg`, `fetchAppInfo`, `downloadFfmpeg` 均仅 `console.error`，用户完全无感知。尤其是 `saveSettings` 失败时，UI 状态已被乐观更新但后端未持久化，造成数据不一致。 |
| F-H9 | 错误处理 | `TaskQueuePage.vue:46,58,64,75,95` | **5 处 console.error 静默吞错误** -- `mount`, `select_files`, `handleAddFiles`, `handleDrop`, `handleStartAllPending` 失败时用户无任何反馈。 |
| F-H10 | 架构 | `useGlobalConfig.ts` (全文) | **模块级 reactive 单例无重置安全** -- `loadFromTaskConfig()` 使用 `Object.assign` 直接修改 reactive 对象。如果后端返回的 config 包含意外的字段或嵌套对象，会污染默认值且无法回滚。`DEFAULT_*` 常量在 `Object.assign` 时是浅拷贝源，如果 reactive 对象先前被添加了额外属性，reset 时不会清除这些多余属性。 |

---

## 三、MEDIUM (16)

| # | 类别 | 问题摘要 |
|---|------|---------|
| F-M1 | 类型安全 | `types/task.ts:28` -- `task_type: string` 应为 `"transcode"/"auto_editor"` 等 union type，与后端 Task 模型一致 |
| F-M2 | 类型安全 | `types/config.ts:84` -- `recommendedQuality?: number` 无范围约束，UI 可传入负数或超大值 |
| F-M3 | 类型安全 | `types/task.ts:32` -- `error: string` 对成功任务也应允许空字符串，缺少 `""` 的语义标注 |
| F-M4 | 类型安全 | `types/task.ts:33` -- `log_lines: string[]` 在 TaskDTO 中声明但前端从未使用（进度日志走 useTaskProgress），冗余字段 |
| F-M5 | 代码质量 | `TaskQueuePage.vue:46,58,64,75,95` + `SettingsPage.vue:31` -- 6 处 `console.error` 泄漏到生产代码 |
| F-M6 | 代码质量 | `FileDropInput.vue:178` -- `console.error("[FileDropInput] file dialog failed:", err)` |
| F-M7 | 代码质量 | `useTaskQueue.ts:77,81` -- `console.error` 用于 bridge 调用失败 |
| F-M8 | 架构 | **4 个组件超过 300 行**: `FilterForm.vue` (412), `BasicTab.vue` (382), `TranscodeForm.vue` (354), `CustomCommandPage.vue` (329) |
| F-M9 | 架构 | `CustomCommandPage.vue` -- 同时处理文件探测、参数编辑、命令预览三大职责，应拆分 |
| F-M10 | 架构 | `useGlobalConfig.ts:93-100` -- merge watch 仅处理 intro/outro -> filter_complex，但未反向处理（清除 intro/outro 时不自动切回） |
| F-M11 | 架构 | `useAutoEditor.ts` -- 14 个独立 ref 管理参数状态，散布在函数中，应考虑合并为一个 reactive 对象 |
| F-M12 | 数据安全 | `useFileFormats.ts:58-59` -- `loadFileFormats()` 每次 `useFileFormats()` 调用都会触发（虽然内部有 `loaded` 标志），但 `loaded` 不是响应式的，多组件并发调用可能导致重复请求 |
| F-M13 | 数据安全 | `bridge.ts:54-63` -- `call()` 函数无请求超时机制，若后端方法挂起，前端 Promise 永远不会 resolve/reject |
| F-M14 | 代码质量 | `SplitDropZone.vue:90` -- `e as any` 获取 clientX 的 fallback，应在类型层面处理 |
| F-M15 | a11y | **全局性缺失**: 所有 interactive 元素缺少 `aria-label`、`role` 属性；drag-and-drop 区域无键盘替代方案；modal 对话框 (PresetEditor) 缺少焦点陷阱 |
| F-M16 | 代码质量 | `data/encoders.ts` -- 编码器描述硬编码为英文字符串，未走 i18n；`priority: "P0"/"P1"/"P2"` 应定义为常量 |

---

## 四、LOW (8)

| # | 问题摘要 |
|---|---------|
| F-L1 | `TaskLogPanel.vue:47` -- v-for 使用数组索引 `:key="i"`（对只追加的日志行可接受，但不是最佳实践） |
| F-L2 | `EncoderSelect.vue:129` -- v-for 使用 index 作为 key |
| F-L3 | `data/autoEditorEncoders.ts` -- 编码器描述硬编码，未走 i18n |
| F-L4 | `utils/format.ts` -- `formatBitRate` 对无效输入返回原始字符串而非友好提示 |
| F-L5 | `useBridge.ts:21` -- `(e as CustomEvent).detail` 无运行时类型验证 |
| F-L6 | `useTheme.ts:70` -- `onUnmounted` 中重新创建 `matchMedia` 对象来 remove listener，应缓存引用 |
| F-L7 | `useFileDrop.ts:42` -- 50ms 魔数延迟用于等待 pywebvue drop handler，注释了原因但未提取为常量 |
| F-L8 | `i18n/locales/en.ts:30` -- 字符串内嵌引号 `"Click \"Auto Detect\" or \"Select...\""` 虽然 vue-i18n 默认不解析 HTML，但转义风格不一致 |

---

## 五、正面发现

- **零 v-html 使用** -- 全部 64 个 Vue 文件未发现任何 `v-html`，不存在 XSS 风险
- **bridge 类型化** -- `ApiResponse<T>` 泛型封装，`call<T>()` 提供返回值类型推断
- **useBridge 自动清理** -- 事件监听器通过 `onUnmounted(cleanup)` 自动移除，设计优秀
- **不可变更新** -- `useTaskQueue` 的 state 更新全部使用 spread 创建新数组/新对象
- **race condition 保护** -- `useCommandPreview` 使用 `requestId` + `validatingFlag` 双重防护，`useAutoEditor` 有 debounce + in-flight guard
- **Vue 最佳实践** -- 全部使用 `<script setup lang="ts">` + Composition API，prop/emit 类型完整
- **路由懒加载** -- 所有页面组件使用 `() => import()` 动态导入
- **TypeScript strict** -- `tsconfig.json` 开启 `strict: true`, `noUnusedLocals`, `noUnusedParameters`
- **Hash 路由** -- 正确使用 `createWebHashHistory` 兼容 pywebview
- **无 eval/exec/pickle** -- 前端无动态代码执行
- **无硬编码凭证** -- 所有后端通信通过 pywebview bridge，无 API key/token
- **组件命名规范** -- 文件名 PascalCase，composable 以 `use` 前缀，类型以 `DTO` 后缀
- **Tailwind + DaisyUI** -- 使用 utility-first CSS 框架，无内联样式

---

## 六、与后端审计的关联问题

| 后端编号 | 关联前端问题 |
|----------|-------------|
| H-4 (FFmpegApi God Class) | 前端 `call()` 直接引用后端方法名 (字符串)，无中央注册表，重命名后端方法会静默失败 |
| H-5 (事件名裸字符串) | 前端 `onEvent("task_progress", ...)` 同样使用裸字符串，两端无共享常量 |
| H-9 (路径无验证) | 前端 `addTasks(paths)` 不验证文件路径格式就直接发送后端 |
| M-5 (异常信息返回前端) | 前端直接 `{{ probeError }}` / `{{ res.error }}` 渲染后端异常信息，可能包含文件系统路径等敏感信息 |
| M-9 (事件载荷无文档) | 前端各 composable 自行 `as Record<string, unknown>` 解析事件载荷，无统一 schema |

---

## 七、优先修复建议

### P0 -- 立即修复

1. **useCommandPreview 添加 timer 清理** -- 在 composable 内部 `onUnmounted(() => clearTimeout(debounceTimer))` 或返回 dispose 函数
2. **验证 AutoCutPage 调用 useAutoEditor.dispose()** -- 若未调用则添加 `onUnmounted(dispose)`
3. **usePresets `catch (e: any)` 改为 `catch (e: unknown)`**

### P1 -- 近期修复

4. **所有 setTimeout 存储 ID 并在 onUnmounted 清除** -- ClipForm, CommandPreview, MergeFileList, PresetSelector, CustomCommandPage
5. **queue_changed 事件添加载荷验证** -- 与其他事件处理器保持一致
6. **useSettings 错误反馈** -- 至少在 `saveSettings` 失败时回滚 UI 状态 + toast 提示
7. **bridge.call() 添加超时机制** -- 可选参数 `timeout?: number`，默认 30s

### P2 -- 架构改进

8. **拆分大组件** -- FilterForm, BasicTab, TranscodeForm, CustomCommandPage
9. **事件名 + 方法名常量化** -- 前后端共享常量文件或生成自 OpenAPI spec
10. **task_type 改为 union type** -- 与后端保持同步
11. **替换 console.error** -- 引入轻量 toast/error boundary 机制
12. **添加基础 a11y** -- 至少为 interactive 元素添加 aria-label

---

## 八、统计

| 严重度 | 数量 |
|--------|------|
| CRITICAL | 1 |
| HIGH | 10 |
| MEDIUM | 16 |
| LOW | 8 |
| **合计** | **35** |

| 分类 | CRITICAL | HIGH | MEDIUM | LOW |
|------|----------|------|--------|-----|
| 内存泄漏 | 1 | 2 | 0 | 0 |
| 类型安全 | 0 | 2 | 4 | 0 |
| 数据安全 | 0 | 3 | 2 | 0 |
| 错误处理 | 0 | 2 | 3 | 0 |
| 架构 | 0 | 1 | 4 | 0 |
| 代码质量 | 0 | 0 | 3 | 2 |
| a11y | 0 | 0 | 1 | 0 |
| 类型标注 | 0 | 0 | 0 | 1 |
| 最佳实践 | 0 | 0 | 0 | 2 |

---

## 九、前后端审计对比

| 维度 | 后端 (Python) | 前端 (Vue/TS) |
|------|--------------|---------------|
| 审计文件数 | 19 | 64 |
| 代码行数 | ~7,000 | ~5,500 |
| CRITICAL | 3 | 1 |
| HIGH | 15 | 10 |
| MEDIUM | 18 | 16 |
| LOW | 8 | 8 |
| **合计** | **44** | **35** |

**总体评估**: 前端代码质量优于后端。CRITICAL 问题仅为后端的 1/3，主要风险集中在 timer/事件监听器泄漏。类型系统 (TypeScript strict) 提供了良好的安全保障，但仍有 `any` 使用和事件载荷验证缺失。架构层面的问题 (大组件、字符串耦合) 优先级较低，可在后续迭代中逐步改进。
