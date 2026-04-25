# Python Code Review Report - 2026-04-25

## Focus: FFmpeg 参数实时预览延迟 & 后端 UX 缺陷

---

## 一、延迟根因分析: FFmpeg 参数修改 -> 命令预览更新

### 数据流全链路

```
用户修改参数 -> Vue reactive state 更新
  -> useGlobalConfig.configRef (computed) 重新求值
  -> useCommandPreview watch 深度监听触发
  -> 300ms debounce 延迟
  -> Promise.all([validate_config, build_command])  // 两次独立的 Bridge API 调用
  -> PyWebView Bridge 跨进程序列化/反序列化
  -> main.py: TaskConfig.from_dict(config)  // 每次重建 frozen dataclass
  -> command_builder.build_command_preview() // 纯字符串拼接
  -> 结果返回前端 -> Vue re-render
```

### 延迟分解 (估算)

| 阶段 | 耗时 | 说明 |
|------|------|------|
| Vue 响应式触发 | ~1ms | watch deep detection |
| Debounce 等待 | 300ms | 固定延迟，不可跳过 |
| Bridge IPC 序列化 (去程) | 10-50ms | PyWebView 跨进程 JSON 序列化 |
| `TaskConfig.from_dict` | ~1ms | frozen dataclass 构建 |
| `build_command_preview` | <1ms | 纯字符串拼接，极快 |
| `validate_config` | <1ms | registry 查表 + 正则匹配 |
| Bridge IPC 反序列化 (回程) | 10-50ms | 反序列化 |
| Vue DOM 更新 | ~5ms | v-if/v-for diff |
| **总计** | **~320-400ms** | |

**结论: 后端 build_command_preview 和 validate_config 都是纯同步计算，总耗时 <2ms。延迟瓶颈不在后端计算，而在前端 debounce 策略和 Bridge IPC 通信架构。**

---

## 二、具体代码问题

### [HIGH] 两次独立 Bridge IPC 可合并为一次

**文件**: `main.py:474-498`, `useCommandPreview.ts:39-42`

当前前端每次参数变化发两次独立请求:

```typescript
// useCommandPreview.ts:39-42
const [valRes, cmdRes] = await Promise.all([
  call<{ errors: string[]; warnings: string[] }>("validate_config", config),
  call<string>("build_command", config),
])
```

虽然 `Promise.all` 让它们并行，但仍然是两次独立的 Bridge IPC 往返（两次序列化 + 两次反序列化）。应合并为单个 `preview_command` 接口，一次往返拿到全部结果，减少 20-100ms。

---

### [HIGH] 命令构建是纯字符串拼接，完全可以前端化实现零延迟预览

**文件**: `command_builder.py` 全文 (1245行), `main.py:474-485`

`build_command_preview` 的核心逻辑是: 遍历 registry 字典 -> 根据 `getattr` 值拼接字符串 -> join 成命令。没有任何 IO、无文件系统访问、无外部进程调用，是纯粹的字符串映射操作。

而 `validate_config` 中仅 watermark 的校验涉及 `Path(val).exists()` (一次文件系统调用)，其余都是正则匹配。

**建议**: 将命令构建逻辑移植一份轻量 TypeScript 版到前端，实现:
- 命令预览: 零延迟（纯前端计算，debounce 降到 50ms 即可）
- 参数校验: 异步调用后端（debounce 可放宽到 500ms，因为校验结果不影响命令显示）

---

### [MEDIUM] 300ms debounce 对所有参数类型一视同仁

**文件**: `useCommandPreview.ts:55-59`

```typescript
function scheduleUpdate() {
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(updatePreview, 300)
}
```

当前所有参数变化都使用同一个 300ms debounce。对于下拉选择（如 codec 切换，不会连续触发），300ms 的等待是不必要的。对于文本输入（如手动输入 bitrate），300ms 可能又不够长，导致频繁 IPC 调用。

**建议**: 区分交互类型，对下拉/开关类操作使用更短的 debounce (50-100ms)，对文本输入使用较长的 debounce (300-500ms)。或将命令构建和校验的 debounce 分离。

---

### [MEDIUM] configRef 每次 computed 都创建完整对象拷贝

**文件**: `useGlobalConfig.ts:77-102`

```typescript
const configRef = computed<TaskConfigDTO>(() => {
  const base: TaskConfigDTO = {
    transcode: { ...transcode },    // 每次展开拷贝
    filters: { ...filters },        // 每次展开拷贝
    output_dir: "",
  }
  // ...根据 activeMode 追加子配置
  return base
})
```

`configRef` 是 computed，任何依赖属性变化时都会重新求值，创建全新的对象。`watch(configRef, ..., { deep: true })` 检测到新对象后触发 debounce。

注意: 浅拷贝本身很快，不是性能瓶颈。但意味着**任何全局状态属性变化（即使与当前 tab 无关）都会触发一次预览更新**。例如如果 `merge.intro_path` 在其他地方被修改（比如全局 intro/outro 设置），也会触发 CommandConfigPage 的预览更新，即便该页面当前在 transcode tab，没有显示 merge 相关的 UI。

---

### [LOW] watch deep 对复合对象的 GC 压力

**文件**: `useCommandPreview.ts:62`

```typescript
watch(configRef, scheduleUpdate, { deep: true, immediate: true })
```

`configRef` 包含 transcode(12字段) + filters(16字段) + 可能的 clip/merge/avsmix/custom 子对象。Vue 的 deep watch 对所有嵌套属性递归设置 getter 代理。由于 `configRef` 是 computed，每次重算返回新对象，旧的 proxy 会被 GC。

当前数据规模下 (~40个字段) 影响可忽略不计，但如果后续扩展（如每滤镜多参数），这个 GC 压力会线性增长。

---

## 三、多页面 useCommandPreview 实例分析

项目中有 4 个页面独立实例化了 `useCommandPreview`:

### 页面架构

| 页面 | 路由 | configRef 来源 | 是否独立状态 |
|------|------|---------------|-------------|
| CommandConfigPage | /config | `useGlobalConfig().toTaskConfig()` (computed) | 共享全局状态 |
| AudioSubtitlePage | /audio-subtitle | `useGlobalConfig().toTaskConfig()` (computed) | 共享全局状态，onMounted 设置 activeMode=avsmix |
| CustomCommandPage | /custom-command | `useGlobalConfig().toTaskConfig()` (computed) | 共享全局状态，onMounted 设置 activeMode=custom |
| MergePage | /merge | 页面内本地 `mergePreviewConfig` (computed) | **本地独立 mergeConfig** |

### 详细分析

**CommandConfigPage, AudioSubtitlePage, CustomCommandPage** 三者共用同一个 `useGlobalConfig` 的全局状态。由于 Vue Router 使用懒加载 (`() => import(...)`)，同一时刻只有一个页面组件存活，所以**不存在多个 watch 同时监听的问题**。页面切换时旧组件卸载 (watch 自动停止)，新组件挂载 (新建 watch)。因此不存在重复 IPC 调用。

这三个页面的差异仅在于 `onMounted` 时设置的 `activeMode` 不同:
- CommandConfigPage: `activeMode = "transcode"` (默认)，tab 切换在页面内部完成
- AudioSubtitlePage: `activeMode = "avsmix"`，configRef 自动带上 avsmix 子配置
- CustomCommandPage: `activeMode = "custom"`，configRef 自动带上 custom_command 子配置

**MergePage 使用本地 mergeConfig**，与 CommandConfigPage 的全局 merge 状态完全独立。这是**有意为之的设计**:
- MergePage 的 `mergeConfig.file_list` 是用户在页面上拖拽添加的实际文件列表
- CommandConfigPage 的 MergeSettings tab 只配置 `target_resolution`、`target_fps`、`intro_path`、`outro_path` 等参数
- MergePage 注释明确写道: *"Independent page for multi-video concatenation. Uses its own local merge config (independent from Config page merge settings)."*

**需要注意的边界**: CommandConfigPage 的 MergeSettings tab 和 MergePage 共享全局 transcode/filters 设置。用户在 MergePage 修改了 transcode 参数后切到 CommandConfigPage，会发现 transcode 设置已同步变更（来自同一个 reactive singleton）。这在当前设计中是合理的（全局共享编码设置），但可能造成轻微的认知困惑。

**结论: 当前的多页面 useCommandPreview 实例化设计是合理的。不存在重复调用或状态冲突问题。**

---

## 四、其他后端 UX 缺陷

### [MEDIUM] add_tasks 中 probe_file 阻塞主线程

**文件**: `main.py:230-257`, `core/file_info.py:11-69`

```python
# main.py:241-257
for path in paths:
    try:
        info = probe_file(path) or {}  # 同步调用 ffprobe，每个文件 50-200ms
        task = Task(...)
        tasks.append(task)
    except Exception as probe_err:
        # fallback
```

`probe_file` 对每个文件同步调用 ffprobe 子进程 (timeout=30s)。当用户批量添加大量文件时:
- 10 个文件: ~0.5-2s 阻塞
- 50 个文件: ~2.5-10s 阻塞
- 如果有无效文件触发 30s timeout: 更严重

PyWebView 的 Bridge 调用在主线程执行，这段期间前端会卡死无响应。

**建议**: 将 probe 改为后台线程批量执行，通过 `_emit` 逐个通知前端任务信息更新。

---

### [MEDIUM] check_hw_encoders 同样阻塞主线程

**文件**: `main.py:505-525`

```python
result = subprocess.run(
    [ffmpeg_path, "-encoders"],
    capture_output=True, text=True, timeout=30,
)
```

在 `onMounted` 中调用，虽然是初始化时一次性执行，但如果 FFmpeg 路径无效或启动慢 (30s timeout)，前端在等待期间无法操作。当前 CommandConfigPage 的 `onMounted` 中有 try-catch 静默处理了这个问题，但用户不会得到任何反馈。

---

### [LOW] validate 返回缺少 param 字段供前端定位

**文件**: `command_builder.py` validate_config 函数

```python
# 内部有 param 字段:
errors.append({"level": item["level"], "param": key, "message": item["message"]})

# 但最终返回时被丢弃:
errors = [i["message"] for i in issues if i["level"] == "error"]
warnings = [i["message"] for i in issues if i["level"] == "warning"]
return {"errors": errors, "warnings": warnings}
```

`validate_config` 内部收集了 `param` 字段 (如 `"video_codec"`, `"crop"`)，但最终返回时只保留了 `message` 字符串。前端 `CommandPreview.vue` 只能显示纯文本错误，无法高亮对应的表单字段或自动切换到出错的 tab。

**建议**: 返回结构化的 `{level, param, message}` 列表，让前端可以联动高亮。

---

### [LOW] watermark validate 在预览模式下执行文件系统检查

**文件**: `command_builder.py` watermark filter registration

```python
validate=lambda val, fc, ctx: (
    [{"level": "error", "message": f"Watermark file not found: {val}"}]
    if not Path(val).exists()  # 每次预览都检查文件是否存在
    ...
)
```

用户在输入水印路径的过程中 (如正在输入一半的路径)，每次 debounce 触发都会检查文件是否存在，产生误导性的 "file not found" 错误。在预览场景下，文件存在性检查可以延迟到实际执行前。

---

### [LOW] _TRANSPILE_PARAMS 使用 callable 类型注解

**文件**: `command_builder.py:80-82`

```python
def _register_transcode_param(
    key: str,
    build: callable,    # 不够精确
    validate: callable, # 不够精确
) -> None:
```

`callable` 是不够精确的类型注解。由于这是内部模块，不影响功能，但如果后续扩展 registry 系统或增加类型检查工具，建议使用更具体的签名。

---

## 五、优化建议优先级

| 优先级 | 优化项 | 预期效果 | 复杂度 |
|--------|--------|----------|--------|
| P0 | 合并 `build_command` + `validate_config` 为单个 `preview_command` API | 减少 20-100ms (一次 IPC 代替两次) | 低 |
| P0 | 分离命令生成和校验的 debounce 频率: 命令 150ms, 校验 500ms | 命令预览延迟从 ~350ms 降到 ~170ms | 低 |
| P1 | 前端实现轻量命令构建 (纯 TS), 后端降级为 validation-only | 命令预览零延迟 (纯前端), 校验异步 | 中 |
| P1 | validate_config 返回结构化 `{param, level, message}` | 支持前端字段高亮和 tab 自动切换 | 低 |
| P2 | add_tasks 中 probe_file 改为后台线程批量执行 | 批量添加文件时前端不再卡死 | 中 |
| P2 | watermark validation 预览模式跳过文件存在检查 | 减少误报 | 低 |
| P3 | 命令构建前端化后可完全移除后端 build_command API | 减少 Bridge 接口数量 | 低 (依赖 P1) |

---

## 六、总结

**延迟根因**: 300ms debounce + 2 次 Bridge IPC 往返。后端 build_command_preview 和 validate_config 本身都是 <1ms 的纯同步计算，不是瓶颈。

**最高性价比优化**:
1. 合并为单次 API 调用 + 分离 debounce 频率 (改动最小，效果明显)
2. 命令预览前端化 (改动较大，但实现零延迟的终极方案)

**多页面实例**: 当前 4 个页面的 useCommandPreview 实例化是合理的。页面通过 Vue Router 懒加载，同一时刻只有一个页面组件存活，不存在重复 watch 或状态冲突。MergePage 使用本地独立 mergeConfig 是有意为之的设计 -- MergePage 管理实际文件列表，CommandConfigPage 的 MergeSettings tab 只管参数配置。

**其他 UX 缺陷**: 批量添加文件时的 probe_file 阻塞、validate 返回缺少 param 定位字段，是影响用户体验的主要后端问题。
