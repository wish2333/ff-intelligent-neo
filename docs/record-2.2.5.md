# 更新记录 v2.2.5

- 日期: 2026-06-07
- 分支: dev-2.2.5
- 类型: 修复 (fix) + 新功能 (feat)

---

## 变更概述

修复音视频混流页字幕 map 索引硬编码错误，新增字幕压制（burn）模式，将特效字幕烧录到画面中。

---

## v2.2.5 变更详情

### 1. 修复字幕 map 索引硬编码错误 (CRITICAL)

**文件**: `core/command_builder.py`

- embed 模式下字幕 map 索引原硬编码为 `2:s`，当音频文件和字幕文件输入顺序变化时会导致 FFmpeg 报错
- 改为根据实际输入文件数量动态计算字幕流的 map 索引

### 2. 新增字幕压制（burn）模式 (feat)

**文件**: `core/models.py`, `core/command_builder.py`, `frontend/src/pages/AudioSubtitlePage.vue`, `frontend/src/types/config.ts`, `frontend/src/i18n/locales/zh-CN.ts`, `frontend/src/i18n/locales/en.ts`

- `AudioSubtitleConfig` 新增 `subtitle_mode` 字段，支持两种模式:
  - `embed` - 软字幕封装（原有行为）
  - `burn` - 字幕压制，使用 FFmpeg `subtitles` 滤镜将字幕烧录到画面中
- burn 模式自动移除 `-c:v copy` 以确保视频重新编码
- 新增 `_ffmpeg_filter_escape_path` 辅助函数处理 Windows 路径中的特殊字符（方括号等）
- 新增 `_inject_subtitle_burn_filter` 支持字幕压制滤镜与现有滤镜链（裁剪/水印等）组合使用
- 前端音视频混流页新增字幕模式单选选择器，支持中英文切换

### 3. 简化 build_avsmix_command 逻辑 (refactor)

**文件**: `core/command_builder.py`

- `build_avsmix_command` 委托给 `build_command`，避免重复的命令构建逻辑

---

## v2.2.4 变更详情（未发布）

### 1. 修复 loadFromTaskConfig 状态残留与模式覆盖 (HIGH)

**文件**: `frontend/src/composables/useGlobalConfig.ts`

- 加载预设或编辑任务时，先重置 clip/merge/avsmix/customCommand 到默认值，再按优先级决定 activeMode
- 优先级: custom > merge(多文件拼接) > avsmix > clip > merge(仅片头片尾) > transcode
- 修复了加载同时包含 clip 和 avsmix 的预设时，activeMode 被最后一个匹配项覆盖的问题

### 2. 新增 createBaseTaskConfig 公共基础配置函数 (LOW)

**文件**: `frontend/src/composables/useGlobalConfig.ts`

- 导出 `createBaseTaskConfig()` 函数，返回包含 transcode + filters + output_dir 的基础 TaskConfigDTO
- MergePage 使用此函数替代手写基础配置，确保所有页面的公共参数源自同一来源

### 3. MergePage 使用公共基础配置 (LOW)

**文件**: `frontend/src/pages/MergePage.vue`

- `handleAddToQueue` 中使用 `createBaseTaskConfig()` 替代手动展开 transcode/filters

### 4. 新增 merge + avsmix 共存校验 (HIGH)

**文件**: `core/command_builder.py`

- `validate_config` 新增跨配置校验:
  - 多文件拼接 (file_list >= 2) + avsmix 共存 -> error（阻断级）
  - 片头片尾 (intro/outro) + avsmix 共存 -> warning（提示级）
- 修复了 merge 和 avsmix 同时存在时 avsmix 被静默忽略、用户无任何提示的问题

### 5. 修复 task_runner 合并优先级策略 (MEDIUM)

**文件**: `core/task_runner.py`

- 原逻辑 `current.merge or incoming.merge` 会导致全局片头片尾覆盖任务本地配置
- 新逻辑采用三层判定:
  1. 多文件拼接任务 (file_list >= 2) -> 保留任务本地配置
  2. 任务自带片头片尾 -> 保留任务本地配置（本地优先）
  3. 无本地 merge 配置 -> 继承全局片头片尾

### 6. 配置页标签重命名 + 使用提示 (LOW)

**文件**: `frontend/src/components/config/MergeSettingsForm.vue`, `frontend/src/i18n/locales/en.ts`, `frontend/src/i18n/locales/zh-CN.ts`

- 配置页标签从 "Merge"/"合并" 更名为 "Intro / Outro"/"片头片尾"
- MergeSettingsForm 顶部新增信息提示横幅，说明全局片头片尾作用范围及与 avsmix 的管线冲突

---

## 变更文件清单

### v2.2.5

| 文件 | 变更类型 |
|------|----------|
| `core/models.py` | 新增字段 |
| `core/command_builder.py` | 修复 + 新增 + 重构 |
| `frontend/src/pages/AudioSubtitlePage.vue` | UI 新增 |
| `frontend/src/types/config.ts` | 类型新增 |
| `frontend/src/i18n/locales/zh-CN.ts` | 文案新增 |
| `frontend/src/i18n/locales/en.ts` | 文案新增 |
| `docs/fields/AudioSubtitleConfig.csv` | 文档更新 |

### v2.2.4（未发布）

| 文件 | 变更类型 |
|------|----------|
| `frontend/src/composables/useGlobalConfig.ts` | 修复 + 新增 |
| `frontend/src/pages/MergePage.vue` | 重构 |
| `core/command_builder.py` | 新增校验 |
| `core/task_runner.py` | 修复 |
| `frontend/src/components/config/MergeSettingsForm.vue` | UI 更新 |
| `frontend/src/i18n/locales/en.ts` | 文案更新 |
| `frontend/src/i18n/locales/zh-CN.ts` | 文案更新 |

---

## Commit Message

### v2.2.5

```
fix: 修复字幕 map 索引错误，新增字幕压制模式

- 修复 embed 模式 map 索引硬编码为 2:s 的 bug，改为动态计算
- 新增 subtitle_mode 字段，支持 embed（软字幕）和 burn（压制）两种模式
- burn 模式使用 FFmpeg subtitles 滤镜将特效字幕烧录到画面中
- burn 模式自动移除 -c:v copy 以确保视频重新编码
- 新增 _ffmpeg_filter_escape_path 处理 Windows 路径中的特殊字符
- 新增 _inject_subtitle_burn_filter 支持与现有滤镜链（裁剪/水印等）组合
- 简化 build_avsmix_command 委托给 build_command 避免重复逻辑
```

### v2.2.4

```
fix: 修复音视频混流与配置页组合冲突逻辑

- 修复 loadFromTaskConfig 状态残留，采用 reset + 优先级链决定 activeMode
- 新增 merge+avsmix 共存校验（concat 为 error，intro/outro 为 warning）
- 修复 task_runner 合并优先级，三层判定防止全局配置覆盖任务本地配置
- 配置页 Merge 标签重命名为 Intro/Outro，新增使用引导提示
- 导出 createBaseTaskConfig 公共函数统一基础配置来源
```

---

## Release Notes (v2.2.4 + v2.2.5 合并发布)

### 修复

- **字幕 map 索引错误**: 修复音视频混流页软字幕模式下，字幕流索引硬编码为 2:s 导致 FFmpeg 报错的问题，改为根据实际输入文件动态计算
- **配置加载状态残留**: 加载预设或编辑任务时，残留的旧模式状态不再干扰当前页面高亮
- **混流静默丢失**: 同时设置片头片尾和音频/字幕混流时，命令预览现在会显示明确的警告提示，而非静默忽略混流设置
- **全局配置覆盖任务配置**: 全局片头片尾不再覆盖队列中已有独立片头片尾的任务配置

### 新功能

- **字幕压制模式**: 音视频混流页新增字幕压制（burn）模式，可将 ASS/SRT 等特效字幕直接烧录到画面中，支持与裁剪/水印等滤镜链组合使用

### 改进

- **配置页标签**: "合并" 标签更名为 "片头片尾"，更准确反映其功能定位
- **使用引导**: 片头片尾设置区域新增信息提示，说明与音频/字幕混流的冲突关系及多视频合并的正确入口
